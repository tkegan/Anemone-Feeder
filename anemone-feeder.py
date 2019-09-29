#!env python

# import from standard python libraries
import configparser
import logging
from random import random, seed

# import from third party libraries
from ndvector import Point, Vector

#import from our code
from model.Anemone import Anemone
from model.Food import Food

# provide defaults... these are fallback values edit configuration file to
# input run parameters
DEFAULT_CONFIG_FILE_PATH = 'config.ini'

# - end conditions
DEFAULT_NUM_TIMESTEPS = 65000
DEFAULT_MIN_NUM_REMAINING_FOOD_PIECES = 500

# - food
DEFAULT_PIECES_FOOD = 1000
DEFAULT_MAX_FOOD_DIFFUSION_PER_TIMESTEP = 0.001

# - anemone
DEFAULT_NUM_TENTACLES = 12
DEFAULT_DISK_RADIUS = 0.15
DEFAULT_DISK_CENTER_X = 0.0
DEFAULT_DISK_CENTER_Y = 0.3 # center in space given tentacle length 0.4
DEFAULT_DISK_CENTER_Z = 0.0
DEFAULT_DISK_NORMAL_VECTOR_X = 0.0
DEFAULT_DISK_NORMAL_VECTOR_Y = 1.0 # straight up
DEFAULT_DISK_NORMAL_VECTOR_Z = 0.0
DEFAULT_TENTACLE_LENGTH = 0.4
DEFAULT_NUM_TENTACLE_ELEMENTS = 10

# - environment
DEFAULT_CURRENT_VECTOR_X = 0.0
DEFAULT_CURRENT_VECTOR_Y = 0.0
DEFAULT_CURRENT_VECTOR_Z = 0.0


class Simulation():
    def __init__(self, config):
        '''
        Using the provided config instantiate a model of an anemone and some
        anemone food
        '''
        # hang on to a reference to the config
        if isinstance(config, configparser.ConfigParser):
            self.config = config
        else:
            raise Exception("Simulation requires a configparser instance as its only parameter")

        # in order to support reproducable runs allow random number generator to be seeded
        if self.config.has_option('simulation', 'random_seed'):
            random_seed = self.config['random_seed']
            logging.debug("Setting random seed to: %s", random_seed)
            seed(random_seed)    # don't care about type

        # initialize the current
        current_x = self.config.getfloat('model', 'current_vector_x', fallback=DEFAULT_CURRENT_VECTOR_X)
        current_y = self.config.getfloat('model', 'current_vector_y', fallback=DEFAULT_CURRENT_VECTOR_Y)
        current_z = self.config.getfloat('model', 'current_vector_z', fallback=DEFAULT_CURRENT_VECTOR_Z)
        self.current = Vector(current_x, current_y, current_z)

        # initalize the food
        self.food = []
        num_pieces_food = self.config.getint('model', 'num_pieces_food', fallback=DEFAULT_PIECES_FOOD)
        logging.debug("Creating %d pieces of food", num_pieces_food)
        for _ in range(0, num_pieces_food):
            x = random()
            y = random()
            z = random()
            logging.debug("Initialized piece of food at: %f, %f, %f", x, y, z)
            self.food.append(Food(x,y,z))

        self.max_diffusion = self.config.getfloat('simulation', 'max_food_diffusion_per_timestep', fallback=DEFAULT_MAX_FOOD_DIFFUSION_PER_TIMESTEP)

        # initialize the anemone
        try:
            num_tentacles = self.config.getint('model', 'num_tentacles', fallback=DEFAULT_NUM_TENTACLES)
            disk_radius = self.config.getfloat('model', 'disk_radius', fallback=DEFAULT_DISK_RADIUS)
            center_x = self.config.getfloat('model', 'disk_center_x', fallback=DEFAULT_DISK_CENTER_X)
            center_y = self.config.getfloat('model', 'disk_center_y', fallback=DEFAULT_DISK_CENTER_Y)
            center_z = self.config.getfloat('model', 'disk_center_z', fallback=DEFAULT_DISK_CENTER_Z)
            center = Point(center_x, center_y, center_z)
            normal_x = self.config.getfloat('model', 'disk_normal_vector_x', fallback=DEFAULT_DISK_NORMAL_VECTOR_X)
            normal_y = self.config.getfloat('model', 'disk_normal_vector_y', fallback=DEFAULT_DISK_NORMAL_VECTOR_Y)
            normal_z = self.config.getfloat('model', 'disk_normal_vector_z', fallback=DEFAULT_DISK_NORMAL_VECTOR_Z)
            orientation = Vector(normal_x, normal_y, normal_z)
            tentacle_length = self.config.getfloat('model', 'tentacle_length', fallback=DEFAULT_TENTACLE_LENGTH)
            num_tenacle_elements = self.config.getint('model', 'num_tentacle_elements', fallback=DEFAULT_NUM_TENTACLE_ELEMENTS)
        except Exception:
            logging.exception("Unable to instantiate anemone model")

        self.anemone = Anemone(num_tentacles, center, disk_radius, orientation, tentacle_length, num_tenacle_elements)


    def run(self):
        '''
        Using the stored config advance the model a set number of timesteps or
        until a specified end condition is met
        '''
        time_index = 1
        max_timesteps = self.config.getint('simulation', 'num_timesteps', fallback=DEFAULT_NUM_TIMESTEPS)
        min_food_pieces_remaining = self.config.getint('simulation', 'min_remaining_food_pieces', fallback=DEFAULT_MIN_NUM_REMAINING_FOOD_PIECES)

        logging.debug("Running for %d steps or until less than %d pieces of food remain", max_timesteps, min_food_pieces_remaining)
        while time_index <= max_timesteps and len(self.food) >= min_food_pieces_remaining:
            logging.info("Advancing to timestep: %s", time_index)
            self.step()
            time_index += 1
        
        logging.info("Run ended after %d timesteps", time_index - 1)
        logging.info("\t%d pieces of food remain", len(self.food))


    def step(self):
        '''
        Advance the model a single time step
        '''
        # randomly move the food to simulate diffusion
        # optionally apply a translation to all food to simulate a current
        for piece in self.food:
            piece.move_by_diffusion(self.max_diffusion)
            piece.move_by_current(self.current)

        self.anemone.move_by_current(self.current)

        # find food near tentacles and remove if anemone is hungry
        for piece in self.food:
            if self.anemone.will_consume(piece):
                self.food.remove(piece)
                logging.info("Anemone consumed piece at: %f, %f, %f", piece.components[0], piece.components[1], piece.components[2])

        # update the current?


    def output(self, filename_increment_indication = None):
        '''
        Output model data as point cloud files
        '''
        if filename_increment_indication:
            anemone_out_file_name = "anemone-{}.xyz".format(filename_increment_indication)
        else:
            anemone_out_file_name = "anemone.xyz"

        self.anemone.to_point_cloud_file(anemone_out_file_name)


# Here is the main entry point.
if __name__ == "__main__":
    # imports only needed whe n invoked directly (not used as library)
    import argparse
    import os.path
    import sys

    # we use arg parse to parse the command line and create a help message
    parser = argparse.ArgumentParser(
        description = "Model the feeding of a sea anemone.",
        epilog = "Author: Tom Egan <tkegan@greenneondesign.com>")
    parser.add_argument("config_file_path",
        nargs = "?",
        default = DEFAULT_CONFIG_FILE_PATH,
        help = "File path to the config file (ini format) to use. See also example-config.ini")
    parser.add_argument("-oi", "--output-initial",
        action = "store_true",
        help = "Output initial model state")
    parser.add_argument("-of", "--output-final",
        action = "store_true",
        help = "Output initial model state")
    parser.add_argument("-o", "--output-directory",
        nargs = "?",
        default = None,
        help = "Output initial model state")
    
    args = parser.parse_args()

    if not os.path.isfile(args.config_file_path):
        sys.exit("Unable to read config from {0}".format(args.config_file_path))

    # Read our Configuration
    settings = configparser.ConfigParser()
    settings.read(args.config_file_path)

    # Setup logging
    if settings.has_option('logging', 'level'):
        if 'critical' == settings['logging']['level']:
            logging.basicConfig(level=logging.CRITICAL)
        elif 'error' == settings['logging']['level']:
            logging.basicConfig(level=logging.ERROR)
        elif 'warning' == settings['logging']['level']:
            logging.basicConfig(level=logging.WARNING)
        elif 'info' == settings['logging']['level']:
            logging.basicConfig(level=logging.INFO)
        elif 'debug' == settings['logging']['level']:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.ERROR)

    # Run the Simulation
    try:
        s = Simulation(settings)
        if args.output_initial:
            s.output('initial')
        s.run()
        if args.output_final:
            s.output('final')
    except Exception:
        logging.exception("Program terminated unexpectedly")

    # Clean up
    logging.shutdown()