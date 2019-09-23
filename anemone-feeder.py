#!env python

# import from standard python libraries
import configparser
import logging
from math import cos, sin, sqrt, tau
from random import choice, random, seed

# import from third party libraries
from ndvector import Point, Vector

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


class Anemone():
    '''
    Model an anemone as a list of tentacles rooted on a disk defined by a
    center point, a normal vector, and a radius
    '''

    def __init__(self, num_tentacles, disk_center, disk_radius, disk_normal_vector, tentacle_length, num_tentacle_elements):
        '''
        Validate parameters, preserve the disk center, normal vector, and
        radius then build list of tentacles
        '''

        # validate num_tentacles 
        if type(num_tentacles) is not int:
            raise TypeError("num_tentacles must be a non zero positive integer")
        if 1 > num_tentacles:
            raise ValueError("num_tentacles must be a non zero positive integer")

        #validate disk_center
        if type(disk_center) is not Point:
            raise TypeError("Anemone disk center must be a Point in the normalized 3D simulation space")
        if 3 != disk_center.dimension:
            raise ValueError("Anemone disk center must be a Point in the normalized 3D simulation space")
        for i in range(3):
            if -1.0 > disk_center.components[i] or 1.0 <= disk_center.components[i]:
                raise ValueError("Anemone disk center must be a Point in the normalized 3D simulation space")

        if type(disk_radius) is float and disk_radius > 0.0 and disk_radius < 1.0:
            self.disk_radius = disk_radius
        else:
            raise ValueError("disk_radius must be a float between 0.0 and 1.0")

        if type(disk_normal_vector) is not Vector:
            raise TypeError("Anemone disk orientation must be a Vector of dimension 3")
        if 3 != disk_normal_vector.dimension:
            raise ValueError("Anemone disk orientation must be a Vector of dimension 3")

        # hang on to normal vector so we can model changing orientation of
        # disk in future
        self.disk_orientation = disk_normal_vector.normalize()

        if type(tentacle_length) is not float or tentacle_length <= 0.0 or tentacle_length >= 1.0:
            raise ValueError("tentacle length must be a float between 0.0 and 1.0")

        if type(num_tentacle_elements) is not int or 0 >= num_tentacle_elements:
            raise ValueError("num_tentacle_elements must be a non zero positive integer")

        # Implementation of solution by ja72, "How to find perpendicular vector to another vector?" https://math.stackexchange.com/q/2672889
        #v_n = { -b*cos(t) - ac / sqrt(a^2 + b^2) * sin(t), a * cos(t) - bc / sqrt(a^2 + b^2) * sin(t), sqrt(a^2 + b^2) * sin(t) }
        self.tentacles = []
        angle_between_tentacles = tau / num_tentacles
        a = disk_normal_vector.components[0]
        b = disk_normal_vector.components[1]
        c = disk_normal_vector.components[2]
        root_a2_b2 = sqrt(a**2 + b**2)
        self.reaction_distance = tentacle_length / num_tentacle_elements
        vector_between_tentacle_sensors = disk_normal_vector * self.reaction_distance
        self.reaction_distance *= 10.0
        logging.debug("sensitive distance: %f", self.reaction_distance)
        logging.debug("Initializing tentacles")
        for i in range(0, num_tentacles):
            theta = i * angle_between_tentacles
            sin_theta = sin(theta)
            cos_theta = cos(theta)
            x = -b * cos_theta - ((a * c) / root_a2_b2) * sin_theta
            y = a * cos_theta - ((b * c) / root_a2_b2) * sin_theta
            z = root_a2_b2 * sin_theta
            v = Vector(x, y, z)
            tentacle_origin = disk_center + v.normalize() * self.disk_radius
            logging.debug("Initialized tentacle at: %f, %f, %f", x, y, z)

            # make a tentacle as a set of Points along the disk normal vector
            tentacle = []
            for j in range(0, num_tentacle_elements):
                tentacle.append(tentacle_origin + (vector_between_tentacle_sensors * float(j)))

            self.tentacles.append(tentacle)


    def will_consume(self, morsel):
        '''
        Check if morsel is within triggering distance of tentacle
        '''
        for tentacle in self.tentacles:
            for sensitive in tentacle:
                vector_to_morsel = sensitive - morsel
                if vector_to_morsel.magnitude < self.reaction_distance:
                    return True
                else:
                    return False


class Food(Point):
    '''
    Model a piece of food, really just a point constrained to a "normalized"
    three (3) dimensional space ie -1.0 < x < 1.0, -1.0 <= y < 1.0,
    -1.0 < z < 1.0
    '''

    def __init__(self, x, y, z):
        '''
        Create a piece of food modeled as a point constrained within the
        "normalized" three (3) dimensional space ie -1.0 < x < 1.0,
        -1.0 <= y < 1.0, -1.0 < z < 1.0 
        '''
        if type(x) is not float or type(y) is not float or type(z) is not float:
            raise TypeError("Initial food position should be specified as floating point values")

        if x < -1.0 or x >= 1.0:
            raise ValueError("Food must be placed within the normalized space -1.0 <= component < 1.0")
        if y < -1.0 or y >= 1.0:
            raise ValueError("Food must be placed within the normalized space -1.0 <= component < 1.0")
        if z < -1.0 or z >= 1.0:
            raise ValueError("Food must be placed within the normalized space -1.0 <= component < 1.0")

        super().__init__(x, y, z)


    def move_by_diffusion(self, max_diffusion):
        '''
        Randomly move no more than max_diffusion in any direction but do not
        allow to to leave normalized space via wrapping

        (float) max_diffusion serves much like the maximum magnitude of a vector
        with a random direction that the piece of food will be moved. For
        efficiency of calculation max_diffusion is a maximum for each vector
        compontent rather than a maximum of the vector.
        '''

        if type(max_diffusion) is not float:
            raise TypeError("max_diffusion should be a floating point value")

        diffusion_speed = max_diffusion * random()
        for i in range(3):
            self.components[i] += diffusion_speed * random() * choice([-1,1])

            # need to insure food don't "leave" by wrapping x and z and limiting y
            while 1.0 <= self.components[i]:
                self.components[i] -= 2.0

            while -1.0 > self.components[i]:
                self.components[i] += 2.0


    def move_by_current(self, current):
        '''
        Move with curent but do not allow to to leave normalized space via
        wrapping
        '''

        if type(current) is not Vector:
            raise TypeError("current should be a Vector value")

        self += current

        # need to insure food don't "leave" by wrapping x and z and limiting y
        for i in range(3):
            while 1.0 <= self.components[i]:
                self.components[i] -= 2.0

            while -1.0 > self.components[i]:
                self.components[i] += 2.0


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
        time_index = 0
        max_timesteps = self.config.getint('simulation', 'num_timesteps', fallback=DEFAULT_NUM_TIMESTEPS)
        min_food_pieces_remaining = self.config.getint('simulation', 'min_remaining_food_pieces', fallback=DEFAULT_MIN_NUM_REMAINING_FOOD_PIECES)

        logging.debug("Running for %d steps or until less than %d pieces of food remain", max_timesteps, min_food_pieces_remaining)
        while time_index < max_timesteps and len(self.food) >= min_food_pieces_remaining:
            logging.info("Advancing to timestep: %s", time_index)
            self.step()
            time_index += 1
        
        logging.info("Run ended after %d timesteps", time_index)
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

        # find food near tentacles and remove if anemone is hungry
        for piece in self.food:
            if self.anemone.will_consume(piece):
                self.food.remove(piece)
                logging.info("Anemone consumed piece at: %f, %f, %f", piece.components[0], piece.components[1], piece.components[2])

        # update the current?


# Here is the main entry point.
if __name__ == "__main__":
    # imports only needed whe n invoked directly (not used as library)
    import argparse
    import os.path
    import sys

    # we use arg parse to parse the command line and create a help message
    parser = argparse.ArgumentParser(
        description='Model the feeding of a sea anemone.',
        epilog="Author: Tom Egan <tkegan@greenneondesign.com>")
    parser.add_argument('config_file_path',
        nargs='?',
        default=DEFAULT_CONFIG_FILE_PATH,
        help='File path to the config file (ini format) to use. See also example-config.ini')
    
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
        s.run()
    except Exception:
        logging.exception("Program terminated unexpectedly")

    # Clean up
    logging.shutdown()