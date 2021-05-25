package mRUBiS.Observations;

import java.util.HashMap;
import java.util.Random;

/**
 * Keeps the hidden utility states of each component and shop.
 * The states are hidden because they are produce by a time series generator (auto-regressive model)
 * that is not visible to controller.
 *  
 * @author Christian Adriano
 *
 */
public class UtilityHiddenState {

	/** key,value pairs in which the key can be a string that concatenates shop and component_type*/
	public HashMap<String,Double> CurrentUtilityStateMap = new HashMap<String,Double>();

	/** holds the utility values that each component should converge to */
	public HashMap<String,Double> ReferenceUtilityStateMap = new HashMap<String,Double>(); 

	/** convergence rate towards the utility of reference */
	private Double theta = 0.1;

	/** rate to compute the variance around the current utility */
	private Double sigma = 1.0;

	/** object to generate Gaussian numbers, initial seed=9876 */
	private Random randomGenerator = new Random(9876);

	/** 
	 * In case one ones to change the standard calibration of the auto-regressive model
	 * @param theta convergence rate towards the utility of reference
	 * @param sigma rate to compute the variance around the current utility
	 */
	public UtilityHiddenState(Double theta, Double sigma, long randomSeed) {
		this.theta =  theta;
		this.sigma = sigma;
		this.randomGenerator =  new Random(randomSeed); 
		//TODO for all components, initialize the ReferenceUtilityStateMap
	}

	/**
	 * An auto-regressive model combined with an Ornstein–Uhlenbeck procedure.
	 * @param reference_utility: value to end with -> utility of a <componenten, failure>
	 * @param theta: how fast to converge -> fixed to 0.1
	 * @return: current utility shifted closer to the reference_utility
	 */
	public Double updateUtility(String shop, String componentType) {

		String key = shop+":"+componentType;
		Double previousUtility = (Double) this.CurrentUtilityStateMap.get(key);
		Double referenceUtility = (Double) this.ReferenceUtilityStateMap.get(key);

		if(previousUtility==null) {
			//TODO obtain reference_utility for componetType at shop
			return(previousUtility);
		}
		else {//Compute the new utility based on previous one

			double variance = this.sigma.doubleValue() * this.randomGenerator.nextGaussian(); //nextGaussian samples from a normal distribution with mean=0,std=1
			double convergence_shift = this.theta.doubleValue() * (referenceUtility.doubleValue() - previousUtility.doubleValue());
			double current_utility = previousUtility.doubleValue() +  convergence_shift + variance;
			return current_utility;
		}
	}


}

}
