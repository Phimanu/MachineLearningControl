package mRUBiS.Observations;

import java.util.LinkedList;
import java.util.List;
import java.util.Set;
import java.util.logging.Level;
import java.util.stream.Collectors;
import java.util.ArrayList;
import java.util.HashMap;

import de.mdelab.morisia.comparch.Architecture;
import de.mdelab.morisia.comparch.Component;
import de.mdelab.morisia.comparch.Issue;
import de.mdelab.morisia.comparch.Rule;
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

	public static String getInitialState(Architecture MRUBIS) {
		String json = "";

		HashMap<String, HashMap<String, HashMap<String, String>>> shopMap = new HashMap<String, HashMap<String, HashMap<String, String>>>();

		for (Tenant shop : MRUBIS.getTenants())
		{
			HashMap<String, HashMap<String, String>> componentMap = new HashMap<String, HashMap<String, String>>();
			shopMap.put(shop.getName(), componentMap);

			for (Component component: shop.getComponents()) {
				
				HashMap<String, String> parameterMap = new HashMap<String, String>();
				parameterMap.put("name", component.getType().getName());
				parameterMap.put("state", component.getState().getName());
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
		}

		try {
			json = new ObjectMapper().writeValueAsString(shopMap);
			return json;
		} catch (JsonProcessingException e) {
			e.printStackTrace();
		}

		return json;

	}

	public static String getComponentsUtility(Architecture MRUBIS, HashMap<String, HashMap<String, HashMap<String, Double>>> issuesToRulesMap){

		String json = "";

		HashMap<String, HashMap<String, HashMap<String, String>>> shopMap = new HashMap<String, HashMap<String, HashMap<String, String>>>();

		for (Tenant shop : MRUBIS.getTenants())
		{

			HashMap<String, HashMap<String, String>> componentMap = new HashMap<String, HashMap<String, String>>();

			List<Issue> issues = MRUBIS.getAnnotations().getIssues();

			for ( Issue issue: issues) {

				Component affectedComponent = issue.getAffectedComponent();
				String affectedComponentType = affectedComponent.getType().getName();
				String failureName = issue.getClass().getSimpleName().replaceAll("Impl", "");
				
				if (issuesToRulesMap.get(failureName).containsKey(affectedComponentType)) {
					HashMap<String, Double> availableRules = issuesToRulesMap.get(failureName).get(affectedComponentType);
					List<String> availableRuleNames = new ArrayList<>(availableRules.keySet());
					List<String> availableRuleCosts = availableRules.values().stream().map( cost -> String.valueOf(cost) ).collect( Collectors.toList() );

					HashMap<String, String> parameterMap = new HashMap<String, String>();

					parameterMap.put("name", affectedComponentType);
					parameterMap.put("state", affectedComponent.getState().getName());
					parameterMap.put("failure_names", failureName.toString());
					parameterMap.put("rule_names", availableRuleNames.toString());
					parameterMap.put("rule_costs", availableRuleCosts.toString());
					parameterMap.put("adt", String.valueOf(affectedComponent.getADT()));
					parameterMap.put("connectivity", String.valueOf(new Double(affectedComponent.getProvidedInterfaces().size() + affectedComponent.getRequiredInterfaces().size())));
					parameterMap.put("importance", String.valueOf(affectedComponent.getTenant().getImportance()));
					parameterMap.put("reliability", String.valueOf(affectedComponent.getType().getReliability()));
					parameterMap.put("criticality", String.valueOf(affectedComponent.getType().getCriticality()));
					parameterMap.put("request", String.valueOf(affectedComponent.getRequest()));
					parameterMap.put("sat_point", String.valueOf(affectedComponent.getType().getSatPoint()));
					parameterMap.put("replica", String.valueOf(affectedComponent.getInUseReplica()));
					parameterMap.put("perf_max", String.valueOf(affectedComponent.getType().getPerformanceMax()));
					parameterMap.put("component_utility", String.valueOf(ArchitectureUtilCal.computeComponentUtility(affectedComponent)));

					componentMap.put(affectedComponent.getUid() , parameterMap);
					
				} else {
					System.out.println("Failed to find rule for issue " + failureName + " affecting component " + affectedComponentType);
					System.out.println("Current issue to rules map: " + issuesToRulesMap.get(failureName));
					System.out.println("Current af comp: " + affectedComponentType);
				}
			

			}

			shopMap.put(shop.getName(), componentMap);

		}

		try {
			json = new ObjectMapper().writeValueAsString(shopMap);
		} catch (JsonProcessingException e) {
			e.printStackTrace();
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




