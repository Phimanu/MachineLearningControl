package mRUBiS_Tasks;

import java.util.LinkedList;
import java.util.List;

import de.mdelab.morisia.comparch.Issue;
import de.mdelab.morisia.comparch.Rule;

public class Input {
public static void selectAction(Issue issue) {
		
	    issue.getAffectedComponent();
	    issue.getAffectedComponent().getType();
	    issue.getAffectedComponent().getTenant().getName(); // shop name
		
		issue.eClass().getName();
	
		//this should be read from input 
		String actionToExecute="RestartComponent";
		
		//Remove all the other possible actions
		List<Rule> actionsToRemove= new LinkedList<Rule>();
		List<Rule> actionToKeep = new LinkedList<Rule>();
		for (Rule rule : issue.getHandledBy()) {
			if(rule.eClass().getName().equals(actionToExecute))
				{actionToKeep.add(rule);
				System.out.print("\n\n  Action Sucssefuylly Added to Execution List ");
				}
			else actionsToRemove.add(rule);
				
		}
		
		
		for (Rule rule : actionsToRemove) {
			rule.setAnnotations(null);
			rule.setHandles(null);
		}

	
		
	}

}
