# import from standard python libraries
import logging
from math import cos, sin, sqrt, tau

# import from third party libraries
from ndvector import Point, Vector

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
        self.center = disk_center

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
        logging.debug("Sensitive distance: %f", self.reaction_distance)
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


    def move_by_current(self, current):
        '''
        Move with curent but do not allow to to leave normalized space via
        wrapping
        '''

        if type(current) is not Vector:
            raise TypeError("current should be a Vector value")

        # update tentacle positions etc based on current TBD


    def to_point_cloud_file(self, filename):
        '''
        Serialize self in a way suitable for output to a point cloud .xyz file

        Parameter:
            filename - a string representing the path to the desired output file

        Throws:
            Exception - if the pathname is invaild or the file already exists
        '''
        with open(filename, 'w') as f:
            f.write(str(self.center))
            f.write("\n")
            for tentacle in self.tentacles:
                for sensitive in tentacle:
                    f.write(str(sensitive))
                    f.write("\n")