import { Store as ReduxStore } from 'redux';

import * as actions from '../actions/reviewer-chooser';
import { UserApi, ExternalReviewerApi, ReviewerApi } from '../api/reviewer';

export class User {
    type: 'user';

    id: number | string;
    full_name: string;
    username: string;

    constructor(id: number | string, full_name: string, username: string) {
        this.id = id;
        this.full_name = full_name;
        this.username = username;
    }

    static fromApi(data: UserApi): User {
        return new User(data.id, data.full_name, data.username);
    }

    display(): string {
        return this.full_name;
    }
}

export class ExternalReviewer {
    type: 'external';

    email: string;

    constructor(email: string) {
        this.email = email;
    }

    static fromApi(data: ExternalReviewerApi): ExternalReviewer {
        return new ExternalReviewer(data.email);
    }

    display(): string {
        return this.email;
    }
}

export class Reviewer {
    id: number;
    inner: User | ExternalReviewer;

    constructor(id: number, inner: User | ExternalReviewer) {
        this.id = id;
        this.inner = inner;
    }

    static fromApi(data: ReviewerApi): Reviewer {
        return new Reviewer(
            data.id,
            data.internal
                ? User.fromApi(data.internal)
                : ExternalReviewer.fromApi(data.external)
        );
    }

    display(): string {
        return this.inner.display();
    }
}

export interface State {
    reviewers: Reviewer[];
}

function initialState(): State {
    return {
        reviewers: []
    };
}

export function reducer(state: State | undefined, action: actions.Action) {
    if (typeof state === 'undefined') {
        state = initialState();
    }

    switch (action.type) {
        case actions.PUT_REVIEWER: {
            let shareIndex: number | null = null;
            let i = 0;
            for (const share of state.reviewers) {
                if (share.id == action.reviewer.id) {
                    shareIndex = i;
                    break;
                }
                i++;
            }

            const newReviewers = state.reviewers.slice();

            if (shareIndex == null) {
                newReviewers.push(action.reviewer);
            } else {
                newReviewers[shareIndex] = action.reviewer;
            }

            state = Object.assign({}, state, { reviewers: newReviewers });

            break;
        }

        case actions.DELETE_REVIEWER: {
            let reviewerIndex: number | null = null;
            let i = 0;
            for (const reviewer of state.reviewers) {
                if (reviewer.id == action.reviewerId) {
                    reviewerIndex = i;
                    break;
                }
                i++;
            }

            if (reviewerIndex != null) {
                const newReviewers = state.reviewers.slice();
                newReviewers.splice(reviewerIndex, 1);
                state = Object.assign({}, state, { reviewers: newReviewers });
            }

            break;
        }
    }

    return state;
}

export type Store = ReduxStore<State, actions.Action>;
