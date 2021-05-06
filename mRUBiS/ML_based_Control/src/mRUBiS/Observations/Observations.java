package mRUBiS.Observations;

import java.util.LinkedList;
import java.util.List;

import de.mdelab.morisia.comparch.Architecture;
import de.mdelab.morisia.comparch.Component;
import de.mdelab.morisia.comparch.Issue;
import de.mdelab.morisia.comparch.Tenant;
import de.mdelab.morisia.selfhealing.ArchitectureUtilCal;

public class Observations {
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




