# MachineLearningControl
Machine Learning-Based Control of Dynamical Systems 
Requirements and Design
Implementation (training) of controllers to steer and stabilize a dynamical system
The dynamica system is a software platform of multi-tenant e-commerce shops

## Implementation of the following packages:
- 1 Non-Linear and Non-Stationary Environment (Identifiability, Stability)
- 2 Environment with Latent States (Observability)
- 3 Transfer Learning within Environemnt Instances (Generalizability under Sparsity)
- 4 Reinforcement Learning Control (Automated Control Synthesis)

## Install procedure for MRUBIS dependencies:

- Eclipse IDE: Update it
- External libraries:
  - Install from http://download.eclipse.org/releases/neon/
    -The GMF libraries, which are model-driven tools to generate graphical editors in the Eclipse IDE.
  - Install from https://www.hpi.uni-potsdam.de/giese/update-site/
     - In the following order:
       - MDELab Workflow/MDELab Workflow
       - MDELab Workflow/MLSDM Interpreter Component
       - SDM Metamodels, Editors, and Interpreters/MLSDM Metamodel Editor Validation
       - SDM Metamodels, Editors, and Interpreters/MLSDM Interpreter Debugger
  - mRubis source code:
     - Clean update your local repository MachineLearningControl
     - Import the following projects in Eclipse:
       - mRUBiS\ML_based_Control
       - mRUBiS\mRUBiS_CompArch_Simulator
       - mRUBiS\CompArch_Metamodel

## Smoke Test!
Run the following class as a Java Application
- Project: Predict_SelfHealing_Utility
- Package: mRubis_Tasks
- Class: Task_1