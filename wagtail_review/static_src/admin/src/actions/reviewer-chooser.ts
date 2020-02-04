import { Reviewer } from '../state/reviewer-chooser';

export const PUT_REVIEWER = 'put-reviewer';
export const DELETE_REVIEWER = 'delete-reviewer';

interface PutReviewerAction {
    type: typeof PUT_REVIEWER;
    reviewer: Reviewer;
}

interface DeleteReviewerAction {
    type: typeof DELETE_REVIEWER;
    reviewerId: number;
}

export type Action = PutReviewerAction | DeleteReviewerAction;

export function putReviewer(reviewer: Reviewer): PutReviewerAction {
    return {
        type: PUT_REVIEWER,
        reviewer
    };
}

export function deleteReviewer(reviewerId: number): DeleteReviewerAction {
    return {
        type: DELETE_REVIEWER,
        reviewerId
    };
}
