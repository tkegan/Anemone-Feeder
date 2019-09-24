# import from standard python libraries
from random import choice, random

# import from third party libraries
from ndvector import Point, Vector


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


    def __str__(self):
        pieces = []
        for piece in self.components:
            pieces.append(str(piece))
        return 'Food ({})'.format(", ".join(pieces))
