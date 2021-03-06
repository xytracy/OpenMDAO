.. _AdvancedUserGuide:

********************
Advanced User Guide
********************

These tutorials cover more advanced topics.
We assume you have read the :ref:`Basic User Guide <UserGuide>` already,
and build from those basics to cover more complex topics that will let you get the most out of the framework.
Within each section the tutorials are designed to be read in order,
but you can choose to read only the sections that are useful to you.


.. _implicit_model_tutorial:

----------------------------------
Models with Implicit Components
----------------------------------

Lots of analyses make use of an implicit formulation such as the mach-area relationship, circuit analysis, finite element models, and CFD.
This tutorial shows you how to define implicit components and integrate those components into larger models.
It also shows you how to use OpenMDAO's Nonlinear Newton solver to converge the models.

    .. toctree::
        :maxdepth: 1

        implicit_comps/defining_icomps.rst
        implicit_comps/implicit_with_balancecomp.rst


----------------------------------------------------
Working with Analytic Derivatives
----------------------------------------------------

    .. toctree::
        :maxdepth: 1

        derivs/partial_derivs_explicit.rst
        derivs/partial_derivs_implicit.rst
        derivs/derivs_of_coupled_systems.rst


