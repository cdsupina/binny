# Review Material Proposals

You are now in material proposal review mode. Your task is to help the user review all pending material proposals.

## Instructions

1. **List all pending proposals** by calling the MCP tool `list_material_proposals`

2. **For each proposal:**
   - The tool will return Rich-formatted panels showing the proposal details
   - Ask the user: "What would you like to do with this proposal? (approve/reject/defer)"
   - Based on their response:
     - **approve**: Call `approve_material` with the proposal_id
     - **reject**: Call `reject_material` with the proposal_id
     - **defer**: Skip to the next proposal

3. **After reviewing all proposals:**
   - Summarize what was approved/rejected
   - Return to normal Binny mode

## Important Notes

- Show ONE proposal at a time and wait for user response
- The Rich panels are already formatted by the MCP tool - just display them
- Always use the exact `proposal_id` from the proposals when approving/rejecting
- If there are no pending proposals, inform the user and return to normal mode

## Response Format

```
Let's review your pending material proposals.

[Rich panel from MCP tool]

What would you like to do with this proposal? (approve/reject/defer)
```

After user responds, process their choice and move to the next proposal.
