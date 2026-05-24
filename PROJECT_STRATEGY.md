# Project Strategy & ROI Analysis

## 1. High-ROI: Automated Triage
**Goal:** Have Hermes profiles autonomously process tasks in the "Triage" column.
**Status:** Ready to implement.
**Next Steps:**
- Create a script that queries `kanban.db` for tasks with `status='triage'`.
- Decompose these tasks into sub-tasks and move them to `todo`.

## 2. High-ROI: Dashboard Enhancements
**Goal:** Improve usability of the visual interface.
**Status:** In Progress.
**Next Steps:**
- Add filtering by assignee and status.
- Implement task search.
- Add "drag and drop" capability (requires frontend overhaul).

## 3. Medium-ROI: CMS Analysis Integration
**Goal:** Integrate the Medicare data analysis into the Jarvis workflow.
**Status:** Functional but isolated.
**Next Steps:**
- Add a dashboard tab for "Analytics".
- Auto-generate the markup distribution report on a schedule.

## 4. Low-ROI (Security): Credential Rotation
**Goal:** Automatically rotate API keys for safety.
**Status:** Placeholder script created.
**Next Steps:**
- Integrate with provider APIs (Anthropic, Gemini) to perform actual rotations.
