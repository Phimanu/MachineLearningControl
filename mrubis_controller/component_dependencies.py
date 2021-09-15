import os
import random

class ComponentDependencyModel:


    def get_reward(self, component_failure_pair, list_of_failings) -> float:
        '''
        This is the important reward function from RL-4-Feedback Control
        :param component_failure_pair: A tuple of component and failure to repair.
        :param list_of_failings: A list of tuples of component and failures which are still failing.
        :return: The reward for the component_failure_pair. A reward of 0 states that the fix fails.
        '''
        component = component_failure_pair[0]
        failure = component_failure_pair[1]

        # Integrate from here
        # Look at data/transition.py
        #
        #
        # Use transitionMat from HERE
        # Integrate failing_probability into reward
        # Compare both approaches: Discount to 0 (like here)
        # AND: Reward * fail_prob
        # Future work: Mrubis failure possibilities
        # - Update the transition_matrix
        # - Intermittent Failures and permanent failures.
        # - Failure dependencies might exist (failure1 -> failure2)
        # - AR + GARCH (non-stationary regimes) in mRubis

        # TODO: Random Choice other "failing" components from TransitionMat, to get failing prob.
        # TODO2: :) Put stuff into other class + file
        # Slide explaining topology
        #


        # get the failing probability
        failing_components = list(set([i[0] for i in list_of_failings]))

        #Check Component Type, then match with Transition Matrix
        failing_probability = self.transition.return_failing_probability(component, failing_components)

        # will the fixing fail?
        if random.random() <= failing_probability:
            # yes, it fails
            return 0
        else:  # no, the fixing will not fail
            # reduce list of possible rewards to the selection
            filtered = self.data[
                (self.data[self.data.columns[0]] == component) & (self.data[self.data.columns[1]] == failure)]

            # select a reward
            sample_value = 0
            if self.environment[0] in ['ARol', 'GARCH']:
                # in the non-stationary enviornment a already used value is removed from the list of possible reward values
                sample_value = filtered.iloc[0][filtered.columns[2]]
                index = filtered.index[0]
                self.data = self.data.drop(index)
            else:
                sample_value = filtered.sample()[self.data.columns[2]].values[0]
            return sample_value

