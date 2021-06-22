package mRUBiS.Observations;

import java.util.LinkedList;
import java.util.List;
import java.util.logging.Level;
import java.util.HashMap;

import de.mdelab.morisia.comparch.Architecture;
import de.mdelab.morisia.comparch.Component;
import de.mdelab.morisia.comparch.Issue;
import de.mdelab.morisia.comparch.Tenant;
import de.mdelab.morisia.comparch.simulator.Capability;
import de.mdelab.morisia.comparch.simulator.ComparchSimulator;
import de.mdelab.morisia.comparch.simulator.InjectionStrategy;
import de.mdelab.morisia.comparch.simulator.impl.Trace_1;
import de.mdelab.morisia.selfhealing.ArchitectureUtilCal;
import de.mdelab.morisia.selfhealing.incremental.EventListener;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

public class Observations {

//	private Architecture mRubis;
//	
//	public Observations(Architecture mRubisInstance) {
//		this.mRubis = mRubisInstance;
//	}

//	public String executionLoop() {
//		// inject failures
//		// attach event listener
//		//loop for RUNS=1
//		this.mRubis.eAdapters().add(new EventListener());
//
//		// set up simulator:
//		String logFile = null;
//		boolean logToConsole = false;
//		ComparchSimulator simulator = ComparchSimulator.FACTORY.createSimulator(Capability.SELF_REPAIR,
//				this.mRubis, 1, Level.CONFIG, logFile, logToConsole);
//		//InjectionStrategy strategy = new testTrace
//		InjectionStrategy strategy = new Trace_1
//				(simulator.getSupportedIssueTypes(), this.mRubis);
//		simulator.setInjectionStrategy(strategy);
//		
//		//System.out.println(Observations.getComponentsUtility());
//		return this.getComponentsUtility();
//	}


	public static String getComponentsUtility(Architecture MRUBIS){


		ArchitectureUtilCal.computeOverallUtility(MRUBIS);
		String json = "";

		for (Tenant shop : MRUBIS.getTenants())
		{ArchitectureUtilCal.computeShopUtility(shop);

		shop.getName();
		shop.getCriticality();
		shop.getPerformance();
		shop.getRequest();

		HashMap<String, HashMap<String, HashMap<String, String>>> shopMap = new HashMap<String, HashMap<String, HashMap<String, String>>>();
		HashMap<String, HashMap<String, String>> componentMap = new HashMap<String, HashMap<String, String>>();
		shopMap.put(shop.getName(), componentMap);

		for ( Component component : shop.getComponents())
		{    

			HashMap<String, String> parameterMap = new HashMap<String, String>();

			parameterMap.put("name", component.getType().getName());
			parameterMap.put("state", component.getState().getName());
			parameterMap.put("health", String.valueOf(component.getHealthStatus()));
			parameterMap.put("adt", String.valueOf(component.getADT()));
			parameterMap.put("connectivity", String.valueOf(new Double(component.getProvidedInterfaces().size() + component.getRequiredInterfaces().size())));
			parameterMap.put("importance", String.valueOf(component.getTenant().getImportance()));
			parameterMap.put("reliability", String.valueOf(component.getType().getReliability()));
			parameterMap.put("criticality", String.valueOf(component.getType().getCriticality()));
			parameterMap.put("request", String.valueOf(component.getRequest()));
			parameterMap.put("sat_point", String.valueOf(component.getType().getSatPoint()));
			parameterMap.put("replica", String.valueOf(component.getInUseReplica()));
			parameterMap.put("perf_max", String.valueOf(component.getType().getPerformanceMax()));
			parameterMap.put("component_utility", String.valueOf(ArchitectureUtilCal.computeComponentUtility(component)));

			componentMap.put(component.getUid() , parameterMap);

		}


		// https://stackoverflow.com/questions/12155800/how-to-convert-hashmap-to-json-object-in-java
		try {
			json = new ObjectMapper().writeValueAsString(shopMap);
			return json;
		} catch (JsonProcessingException e) {
			e.printStackTrace();
		}


		}

		return json;

	}

	public static void makeObservation(Architecture mRUBiS){


		ArchitectureUtilCal.computeOverallUtility(mRUBiS);

		for (Tenant shop : mRUBiS.getTenants())
		{ArchitectureUtilCal.computeShopUtility(shop);

		shop.getName();
		shop.getCriticality();
		shop.getPerformance();
		shop.getRequest();


		for ( Component component : shop.getComponents())
		{    ArchitectureUtilCal.computeComponentUtility(component);
		component.getInUseReplica();
		component.getIssues();
		component.getType();
		component.getCriticality();
		}

		}


		List<Issue> allIssues = new LinkedList<>();
		allIssues.addAll(mRUBiS.getAnnotations().getIssues());
		for (Issue issue : allIssues)
		{issue.getAffectedComponent();
		issue.getUtilityDrop();
		issue.getHandledBy();
		issue.getHandledBy().get(0).getCosts();}

	}
}




