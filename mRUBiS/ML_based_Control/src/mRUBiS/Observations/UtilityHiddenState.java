package mRUBiS.Observations;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Map.Entry;
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
	
	 /** determines how far from the "referenceUtility" should we start. 
	  * The default is 1.5, which implies a 150% of the reference utility value*/
	private Double delta = 1.5; 

	/** 
	 * In case one ones to change the standard calibration of the auto-regressive model
	 * @param theta convergence rate towards the utility of reference
	 * @param sigma rate to compute the variance around the current utility
	 * @param randomSeed initial seed to add noise to the auto-regressive model that updates the utility of each component
	 * @param delta determines how far from the "referenceUtility" should we start
	 */
	public UtilityHiddenState(Double theta, Double sigma, long randomSeed, Double delta) {
		this.theta =  theta;
		this.sigma = sigma;
		this.randomGenerator =  new Random(randomSeed); 
		this.delta = delta;
		this.intilializeReferenceUtilityMap();
		this.initializeCurrentUtilityMap();
	}
	

	/**
	 * For all components of the mRubis instance, 
	 * obtain their utility values and store under a key "shop:componentType"
	 */
	private void intilializeReferenceUtilityMap() {
		//TODO for all components, initialize the ReferenceUtilityStateMap
	}

	
	/**
	 * For each component in the ReferenceUtilityStateMap:
	 * currentUtility = referenceUtility * this.delta
	 */
	private void initializeCurrentUtilityMap() {
		// Getting an iterator
        Iterator<Entry<String, Double>> hmIterator = this.ReferenceUtilityStateMap.entrySet().iterator();
  
        // Iterate through the hashmap
        // and add some bonus marks for every student
        System.out.println("HashMap after adding bonus marks:");
  
        while (hmIterator.hasNext()) {
            Map.Entry mapElement = (Map.Entry)hmIterator.next();
            String key = ((String)mapElement.getKey());
            Double referenceUtility = ((Double)mapElement.getValue());
            Double currentUtility = referenceUtility * this.delta;
            this.CurrentUtilityStateMap.put(key,currentUtility);
        }
	}

	/**
	 * Implements the auto-regressive model combined with an Ornstein–Uhlenbeck procedure.
	 * @param shop: the key name of a shop
	 * @param componetType: the key name of a component type
	 * @return: currentUtility which is a utility shifted closer to the referenceUtility
	 */
	public Double updateCurrentUtility(String shop, String componentType) {

		String key = shop+":"+componentType;
		Double previousUtility = (Double) this.CurrentUtilityStateMap.get(key);
		Double referenceUtility = (Double) this.ReferenceUtilityStateMap.get(key);

		if(previousUtility==null) {
			//TODO obtain reference_utility for componetType at shop
			return(previousUtility);
		}
		else {//Compute the new utility based on previous one

			double variance = this.sigma.doubleValue() * this.randomGenerator.nextGaussian(); //nextGaussian samples from a normal distribution with mean=0,std=1
			double convergenceShift = this.theta.doubleValue() * (referenceUtility.doubleValue() - previousUtility.doubleValue());
			double currentUtility = previousUtility.doubleValue() +  convergenceShift + variance;
			
			//Stores new state
			this.CurrentUtilityStateMap.put(key,currentUtility);
			
			return currentUtility;
		}
	}
	
	/**
	 * Allows to reset the current utility of particular component. 
	 * This happens when a component has been restarted.
	 * @param shop
	 * @param componentType
	 */
	public void resetUtilityState(String shop, String componentType) {
		String key = shop+":"+componentType;
		Double referenceUtility = (Double) this.ReferenceUtilityStateMap.get(key);
		this.CurrentUtilityStateMap.put(key,referenceUtility*this.delta);		
	}


}
