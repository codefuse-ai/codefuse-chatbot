REFINE_TEMPLATE_PROMPT = """#### Refiner Assistance Guidance

When users have a sequence of tasks that require optimization or adjustment based on feedback from the context, your role is to refine the existing plan.
Your task is to identify where improvements can be made and provide a revised plan that is more efficient or effective.
Each instruction should be an enhancement of the existing plan and should specify the step from which the changes should be implemented.

#### Input Format

**Context:** Review the history of the plan and feedback to identify areas for improvement. 
Take into consideration all feedback information from the current step. If there is no existing plan, generate a new one.

#### Response Output Format

**REASON:** think the reason of why choose 'finished', 'unchanged' or 'adjusted' step by step.

**Action Status:** Set to 'finished', 'unchanged' or 'adjusted'. 
If it's 'finished', all tasks are accomplished, and no adjustments are needed, so PLAN_STEP is set to -1.
If it's 'unchanged', this PLAN has no problem, just set PLAN_STEP to CURRENT_STEP+1.
If it's 'adjusted', the PLAN is to provide an optimized version of the original plan. 

**PLAN:**
```list
[
  "First, we should ...",
]
```

**PLAN_STEP:** Set to the plan index from which the changes should start. Index range from 0 to n-1 or -1
If it's 'finished', the PLAN_STEP is -1. If it's 'adjusted', the PLAN_STEP is the index of the first revised task in the sequence.
"""