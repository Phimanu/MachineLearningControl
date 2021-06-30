package mRUBiS.Observations;

import java.util.LinkedList;
import java.util.List;
import java.util.logging.Level;
import java.util.stream.Collectors;
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

	public static String getComponentsUtility(Architecture MRUBIS, HashMap<Issue, List<Rule>> issueToRulesMap){

		String json = "";

		for (Tenant shop : MRUBIS.getTenants())
		{

			HashMap<String, HashMap<String, HashMap<String, String>>> shopMap = new HashMap<String, HashMap<String, HashMap<String, String>>>();
			HashMap<String, HashMap<String, String>> componentMap = new HashMap<String, HashMap<String, String>>();
			shopMap.put(shop.getName(), componentMap);
			
			List<Issue> issues = MRUBIS.getAnnotations().getIssues();
			
			for ( Issue issue: issues) {
				
				Component affectedComponent = issue.getAffectedComponent();
				String failureName = issue.getClass().getSimpleName().replaceAll("Impl", "");
				List<Rule> availableRules = issueToRulesMap.get(issue);
				List<String> availableRuleNames = availableRules.stream().map( rule -> rule.getClass().getSimpleName().replaceAll("Impl", "")).collect( Collectors.toList() );
				List<String> availableRuleCosts = availableRules.stream().map( rule -> String.valueOf(rule.getCosts())).collect( Collectors.toList() );
				
				HashMap<String, String> parameterMap = new HashMap<String, String>();
				
				parameterMap.put("name", affectedComponent.getType().getName());
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
				
			}


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




