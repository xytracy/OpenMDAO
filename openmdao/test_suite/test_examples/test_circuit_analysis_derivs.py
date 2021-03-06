import unittest

from openmdao.devtools.testutil import assert_rel_error

import numpy as np

from openmdao.api import ExplicitComponent, ImplicitComponent, NewtonSolver, DirectSolver, ArmijoGoldsteinLS
from openmdao.api import IndepVarComp, Problem, Group


class TestNonlinearCircuit(unittest.TestCase):

    def test_nonlinear_circuit_analysis(self):
        import numpy as np

        from openmdao.api import ExplicitComponent, ImplicitComponent,  NewtonSolver, DirectSolver, ArmijoGoldsteinLS
        from openmdao.api import IndepVarComp, Problem, Group

        class Resistor(ExplicitComponent):
            def initialize(self):
                self.metadata.declare('R', default=1., desc='Resistance in Ohms')

            def setup(self):
                self.add_input('V_in', units='V')
                self.add_input('V_out', units='V')
                self.add_output('I', units='A')

                # partial derivs are constant, so we can assign their values in setup
                R = self.metadata['R']
                self.declare_partials('I', 'V_in', val=1 / R)
                self.declare_partials('I', 'V_out', val=-1 / R)

            def compute(self, inputs, outputs):
                deltaV = inputs['V_in'] - inputs['V_out']
                outputs['I'] = deltaV / self.metadata['R']


        class Diode(ExplicitComponent):
            def initialize(self):
                self.metadata.declare('Is', default=1e-15, desc='Saturation current in Amps')
                self.metadata.declare('Vt', default=.025875, desc='Thermal voltage in Volts')

            def setup(self):
                self.add_input('V_in', units='V')
                self.add_input('V_out', units='V')
                self.add_output('I', units='A')

                # non-linear component, so we'll declare the partials here but compute them in compute_partials
                self.declare_partials('I', 'V_in')
                self.declare_partials('I', 'V_out')

            def compute(self, inputs, outputs):
                deltaV = inputs['V_in'] - inputs['V_out']
                Is = self.metadata['Is']
                Vt = self.metadata['Vt']
                outputs['I'] = Is * np.exp(deltaV / Vt - 1)

            def compute_partials(self, inputs, J):
                deltaV = inputs['V_in'] - inputs['V_out']
                Is = self.metadata['Is']
                Vt = self.metadata['Vt']
                I = Is*np.exp(deltaV/Vt-1)

                J['I', 'V_in'] = I/Vt
                J['I', 'V_out'] = -I/Vt

        class Node(ImplicitComponent):
            def initialize(self):
                self.metadata.declare('n_in', default=1, type_=int, desc='number of connections with + assumed in')
                self.metadata.declare('n_out', default=1, type_=int, desc='number of current connections + assumed out')

            def setup(self):
                self.add_output('V', val=5., units='V')

                for i in range(self.metadata['n_in']):
                    i_name = 'I_in:{}'.format(i)
                    self.add_input(i_name, units='A')
                    self.declare_partials('V', i_name, val=1)

                for i in range(self.metadata['n_out']):
                    i_name = 'I_out:{}'.format(i)
                    self.add_input(i_name, units='A')
                    self.declare_partials('V', i_name, val=-1)

                    # note: we don't declare any partials wrt `V` here,
                    #      because the residual doesn't directly depend on it

            def apply_nonlinear(self, inputs, outputs, residuals):
                residuals['V'] = 0.
                for i_conn in range(self.metadata['n_in']):
                    residuals['V'] += inputs['I_in:{}'.format(i_conn)]
                for i_conn in range(self.metadata['n_out']):
                    residuals['V'] -= inputs['I_out:{}'.format(i_conn)]

        class Circuit(Group):

            def setup(self):
                self.add_subsystem('n1', Node(n_in=1, n_out=2), promotes_inputs=[('I_in:0', 'I_in')])
                self.add_subsystem('n2', Node())  # leaving defaults

                self.add_subsystem('R1', Resistor(R=100.), promotes_inputs=[('V_out', 'Vg')])
                self.add_subsystem('R2', Resistor(R=10000.))
                self.add_subsystem('D1', Diode(), promotes_inputs=[('V_out', 'Vg')])

                self.connect('n1.V', ['R1.V_in', 'R2.V_in'])
                self.connect('R1.I', 'n1.I_out:0')
                self.connect('R2.I', 'n1.I_out:1')

                self.connect('n2.V', ['R2.V_out', 'D1.V_in'])
                self.connect('R2.I', 'n2.I_in:0')
                self.connect('D1.I', 'n2.I_out:0')

                self.nonlinear_solver = NewtonSolver()
                self.linear_solver = DirectSolver()

                self.nonlinear_solver.options['iprint'] = 2
                self.nonlinear_solver.options['maxiter'] = 10
                self.nonlinear_solver.options['solve_subsystems'] = True
                self.nonlinear_solver.linesearch = ArmijoGoldsteinLS()
                self.nonlinear_solver.linesearch.options['maxiter'] = 10
                self.nonlinear_solver.linesearch.options['iprint'] = 2


        p = Problem()
        model = p.model

        model.add_subsystem('ground', IndepVarComp('V', 0., units='V'))
        model.add_subsystem('source', IndepVarComp('I', 0.1, units='A'))
        model.add_subsystem('circuit', Circuit())

        model.connect('source.I', 'circuit.I_in')
        model.connect('ground.V', 'circuit.Vg')

        p.setup()

        # set some initial guesses
        p['circuit.n1.V'] = 10.
        p['circuit.n2.V'] = 1e-3

        p.run_model()

        assert_rel_error(self, p['circuit.n1.V'], 9.90830282, 1e-5)
        assert_rel_error(self, p['circuit.n2.V'], 0.73858486, 1e-5)
        assert_rel_error(self, p['circuit.R1.I'], 0.09908303, 1e-5)
        assert_rel_error(self, p['circuit.R2.I'], 0.00091697, 1e-5)
        assert_rel_error(self, p['circuit.D1.I'], 0.00091697, 1e-5)
        # 'Sanity check: shoudl sum to .1 Amps
        assert_rel_error(self, p['circuit.R1.I'] + p['circuit.D1.I'], .1, 1e-6)


if __name__ == "__main__":
    unittest.main()