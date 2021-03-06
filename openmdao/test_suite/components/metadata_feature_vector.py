"""
Component for a metadata feature test.
"""
import numpy as np

from openmdao.api import ExplicitComponent


class VectorDoublingComp(ExplicitComponent):

    def initialize(self):
        self.metadata.declare('size', type_=int)

    def setup(self):
        size = self.metadata['size']

        self.add_input('x', shape=size)
        self.add_output('y', shape=size)
        self.declare_partials('y', 'x', val=2., rows=np.arange(size), cols=np.arange(size))

    def compute(self, inputs, outputs):
        outputs['y'] = 2 * inputs['x']
