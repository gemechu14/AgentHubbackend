# Admin/Owner Direct Survey Submission - Implementation Guide

## Overview

This document explains how to allow logged-in Admin/Owner users to submit survey responses directly without requiring an invitation token, while also handling cases where an invitation was already sent to their email.

## Problem Statement

Currently, survey submissions require:
- A valid invitation token
- The token must be extracted from the URL and sent in the request body

**Requirements:**
1. Allow logged-in Admin/Owner users to submit responses without an invitation
2. Handle the case where an invitation was sent to their email but they want to submit directly
3. Add a UI button for Admin/Owner to submit survey responses

## Solution Architecture

### 1. New Authenticated Endpoint

**Endpoint:** `POST /accounts/{account_id}/surveys/{survey_id}/submit`

**Authentication:** Required (Bearer token)
**Authorization:** Only OWNER or ADMIN role for the account
**Location:** `app/api/routes/surveys.py` (authenticated routes, not public routes)

**Key Differences from Public Endpoint:**
- No token required in request body
- Uses authenticated user's email instead of invite email
- Automatically creates or reuses a `SurveyInvite` for the user
- Same response format as public endpoint

### 2. Request/Response Schema

**Request Body:** `SurveySubmitBody` (same as public endpoint, but `token` field is optional/ignored)
```json
{
  "response_data": {
    "rows": [...],
    // or "columns": {...}
  },
  "action": "ADD_NEW" | "UPDATE_LATEST"  // optional, defaults to ADD_NEW
}
```

**Response:** `SurveySubmitResponse` (same as public endpoint)
```json
{
  "response_id": "uuid",
  "action_taken": "added_new" | "updated_latest",
  "submission_count": 5
}
```

### 3. Implementation Logic Flow

#### Step 1: Validate User and Survey Access
```
1. Get authenticated user from JWT token (via `current_user` dependency)
2. Verify user has OWNER or ADMIN role for the account (via `require_role_for_account`)
3. Verify survey exists and belongs to the account
4. Verify survey is ACTIVE and not expired
```

#### Step 2: Find or Create SurveyInvite
```
1. Check if a SurveyInvite exists for:
   - survey_id = survey.id
   - email = user.email (normalized to lowercase)
   
2. If invite exists:
   - Use existing invite
   - Check if invite is revoked (if revoked, raise error)
   - Check if invite is expired (if expired, extend expiry or raise error)
   - Note: Even if invitation was sent, we allow direct submission
   
3. If invite does NOT exist:
   - Create a new SurveyInvite:
     * survey_id = survey.id
     * email = user.email
     * token_hash = generate token (for consistency, even though not needed)
     * expires_at = survey.expires_at OR invite default expiry
     * created_at = now()
     * sent_at = NULL (no email sent)
     * opened_at = NULL (will be set on first open)
     * submitted_at = NULL (will be updated after submission)
     * revoked_at = NULL
```

#### Step 3: Submit Response (Reuse Existing Logic)
```
1. Use the same submission logic as public endpoint:
   - Validate response_data against schema
   - Transform columnar to row format if needed
   - Handle ADD_NEW vs UPDATE_LATEST action
   - Store in database or cloud storage
   - Update invite.submitted_at
   - Return submission count and action taken
```

### 4. Edge Cases and Considerations

#### Case 1: Invitation Already Sent
**Scenario:** Admin sends invitation to their own email, then wants to submit directly.

**Solution:**
- Find existing invite by email
- Use existing invite (don't create duplicate)
- Allow submission even if `sent_at` is set
- This maintains data consistency (one invite per email per survey)

#### Case 2: Invitation Revoked
**Scenario:** Admin revoked their own invitation, then tries to submit directly.

**Options:**
- **Option A (Recommended):** Allow submission, but un-revoke the invite
  - Set `revoked_at = NULL` when Admin/Owner submits directly
  - This makes sense because Admin/Owner should have full control
  
- **Option B:** Block submission and return error
  - Return 403: "Your invitation has been revoked. Please create a new invitation."
  - Less user-friendly but more strict

**Recommendation:** Option A - Auto-unrevoke for Admin/Owner direct submissions.

#### Case 3: Invitation Expired
**Scenario:** Invitation expired, but survey is still active.

**Options:**
- **Option A (Recommended):** Extend invitation expiry
  - Set `expires_at = survey.expires_at OR (now + default_expiry_days)`
  - Admin/Owner should be able to submit as long as survey is active
  
- **Option B:** Block submission
  - Return 403: "Your invitation has expired"
  - Less user-friendly

**Recommendation:** Option A - Auto-extend expiry for Admin/Owner direct submissions.

#### Case 4: Multiple Submissions
**Scenario:** Admin submits directly, then later uses the invitation link.

**Solution:**
- Both submissions use the same `SurveyInvite` record
- Submission count includes both
- `allow_multiple_submissions` flag applies (if False, second submission would be blocked)
- This is consistent behavior

#### Case 5: Survey Closed/Expired
**Scenario:** Admin tries to submit to a closed or expired survey.

**Solution:**
- Check survey status and expiry before allowing submission
- Return 403: "This survey is no longer accepting responses"
- Same validation as public endpoint

### 5. Database Considerations

**No Schema Changes Required:**
- `SurveyInvite` table already supports:
  - `email` (can be Admin/Owner email)
  - `sent_at = NULL` (for direct submissions, no email sent)
  - All other fields work as-is

**Data Integrity:**
- One `SurveyInvite` per email per survey (enforced by unique constraint if exists)
- All submissions linked to same invite (consistent tracking)
- Submission count includes both direct and token-based submissions

### 6. Frontend Implementation

#### UI/UX Flow

**Location:** Survey detail/view page (where Admin/Owner can see survey info)

**Button Placement:**
- Add a "Submit Response" button in the survey actions area
- Only visible if:
  - User is OWNER or ADMIN
  - Survey is ACTIVE
  - Survey is not expired

**Button States:**
- **Enabled:** Survey is active and not expired
- **Disabled:** Survey is closed or expired (with tooltip explaining why)

**Submission Flow:**
1. User clicks "Submit Response" button
2. Frontend opens a modal/dialog with the survey form (same as public survey form)
3. User fills out the form
4. On submit:
   - If user has previous submissions:
     - Show radio buttons: "Add as new response" or "Update latest response"
     - Default to "Add as new response"
   - If no previous submissions:
     - Just show submit button (no choice needed)
5. Call authenticated endpoint: `POST /accounts/{account_id}/surveys/{survey_id}/submit`
6. Show success message with submission count

**API Call Example:**
```javascript
// Frontend code (pseudo-code)
async function submitSurveyResponse(surveyId, responseData, action = 'ADD_NEW') {
  const response = await fetch(
    `/api/accounts/${accountId}/surveys/${surveyId}/submit`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        response_data: responseData,
        action: action  // 'ADD_NEW' or 'UPDATE_LATEST'
      })
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to submit survey');
  }
  
  return await response.json();
}
```

#### UI Components Needed

1. **Submit Response Button**
   - Location: Survey detail page, actions section
   - Styling: Primary button style
   - Icon: Plus icon or submit icon

2. **Survey Form Modal/Dialog**
   - Reuse existing survey form component (used for public submissions)
   - Same validation and schema rendering
   - Add action selector if previous submissions exist

3. **Submission Success Message**
   - Show action taken ("Added new response" or "Updated latest response")
   - Show total submission count
   - Option to view responses

### 7. API Endpoint Details

**Endpoint:** `POST /accounts/{account_id}/surveys/{survey_id}/submit`

**Dependencies:**
- `current_user` (from `app.api.deps_auth`)
- `require_role_for_account({Role.OWNER, Role.ADMIN})`
- `get_db`

**Request Body:**
```python
class SurveySubmitBody(BaseModel):
    response_data: Dict[str, Any]  # Same as public endpoint
    action: Optional[SubmissionAction] = SubmissionAction.ADD_NEW
    # Note: token field is NOT included (not needed for authenticated endpoint)
```

**Response:**
```python
class SurveySubmitResponse(BaseModel):
    response_id: Optional[UUID]
    action_taken: str  # "added_new" or "updated_latest"
    submission_count: int
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: User is not OWNER/ADMIN, or survey is closed/expired
- `404 Not Found`: Survey not found or doesn't belong to account
- `400 Bad Request`: Invalid response data or schema validation failed
- `500 Internal Server Error`: Database or storage error

### 8. Code Structure

**File:** `app/api/routes/surveys.py`

**Function Signature:**
```python
@router.post(
    "/{survey_id}/submit",
    response_model=SurveySubmitResponse,
    summary="Submit survey response (Admin/Owner only)",
    description="""
    Submit a survey response as a logged-in Admin/Owner.
    No invitation token required.
    
    - Automatically creates or reuses a SurveyInvite for the user's email
    - Supports ADD_NEW and UPDATE_LATEST actions
    - Same validation and storage logic as public endpoint
    """
)
def submit_survey_as_admin(
    account_id: UUID,
    survey_id: UUID,
    body: SurveySubmitBody,
    tup=Depends(require_role_for_account({Role.OWNER, Role.ADMIN})),
    db: Session = Depends(get_db),
):
    user, _aid, _role = tup
    # Implementation here
```

**Helper Function:**
```python
def get_or_create_survey_invite_for_user(
    db: Session,
    survey: Survey,
    user_email: str,
    default_expires_at: datetime
) -> SurveyInvite:
    """
    Find existing SurveyInvite for user's email, or create a new one.
    
    - If invite exists but is revoked, un-revoke it
    - If invite exists but is expired, extend expiry
    - If invite doesn't exist, create new one (without sending email)
    """
    # Implementation here
```

### 9. Testing Scenarios

1. **New Submission (No Existing Invite)**
   - Admin submits response
   - Verify new `SurveyInvite` created with `sent_at = NULL`
   - Verify response stored correctly
   - Verify submission_count = 1

2. **Submission with Existing Invite (Not Sent)**
   - Admin creates survey with their email in invite list
   - Admin submits directly (before email is sent)
   - Verify existing invite is reused
   - Verify response stored correctly

3. **Submission with Existing Invite (Already Sent)**
   - Admin creates survey, invitation email sent
   - Admin submits directly
   - Verify existing invite is reused
   - Verify both submissions tracked under same invite

4. **Revoked Invite**
   - Admin revokes their own invitation
   - Admin submits directly
   - Verify invite is un-revoked
   - Verify submission succeeds

5. **Expired Invite**
   - Invite expired but survey still active
   - Admin submits directly
   - Verify invite expiry is extended
   - Verify submission succeeds

6. **Multiple Submissions**
   - Admin submits directly (ADD_NEW)
   - Admin submits again (UPDATE_LATEST)
   - Verify first submission marked as not latest
   - Verify second submission is latest
   - Verify submission_count = 2

7. **Closed Survey**
   - Survey status = CLOSED
   - Admin tries to submit
   - Verify 403 error returned

8. **Expired Survey**
   - Survey expires_at < now
   - Admin tries to submit
   - Verify 403 error returned

9. **Non-Admin User**
   - MEMBER or VIEWER tries to submit
   - Verify 403 error returned

### 10. Migration Considerations

**No Database Migration Required:**
- All necessary fields already exist in `SurveyInvite` table
- `sent_at = NULL` is valid (means no email was sent)

**Backward Compatibility:**
- Public endpoint (`/surveys/submit`) remains unchanged
- Existing token-based submissions continue to work
- New authenticated endpoint is additive (doesn't break existing functionality)

### 11. Security Considerations

1. **Authorization:**
   - Only OWNER/ADMIN can use authenticated endpoint
   - Verify user has access to the account
   - Verify survey belongs to the account

2. **Email Validation:**
   - Use authenticated user's email (from JWT token)
   - Don't allow user to specify a different email
   - This prevents privilege escalation

3. **Survey Access:**
   - Verify survey belongs to the account
   - Verify survey is not deleted
   - Verify survey is active and not expired

4. **Rate Limiting:**
   - Consider rate limiting for authenticated endpoint
   - Prevent abuse (though less likely for authenticated users)

### 12. Summary

**Key Points:**
1. Create new authenticated endpoint: `POST /accounts/{account_id}/surveys/{survey_id}/submit`
2. Automatically find or create `SurveyInvite` for user's email
3. Reuse existing submission logic (validation, storage, etc.)
4. Handle edge cases: revoked invites, expired invites, existing invites
5. Add UI button for Admin/Owner to submit responses
6. No database schema changes required

**Benefits:**
- Admin/Owner can test surveys without sending invitations
- Admin/Owner can submit responses directly from the dashboard
- Maintains data consistency (one invite per email per survey)
- Backward compatible (public endpoint unchanged)

**Next Steps:**
1. Implement authenticated endpoint in `app/api/routes/surveys.py`
2. Add helper function to get/create invite for user
3. Update frontend to add "Submit Response" button
4. Test all edge cases
5. Update API documentation









