export interface UserApi {
    id: number | string;
    full_name: string;
    username: string;
}

export interface ExternalReviewerApi {
    email: string;
}

interface ReviewerApi_Internal {
    id: number;
    internal: UserApi;
    external: null;
}

interface ReviewerApi_External {
    id: number;
    internal: null;
    external: ExternalReviewerApi;
}

export type ReviewerApi = ReviewerApi_Internal | ReviewerApi_External;

export interface NewReviewerSuccess {
    status: 'ok';
    reviewer: ReviewerApi;
}

export interface NewReviewerValidationError {
    status: 'error';
    email?: string;
}

export type NewReviewerResponse =
    | NewReviewerSuccess
    | NewReviewerValidationError;

export default class ReviewerAPIClient {
    async getUsers({ search }: { search?: string }): Promise<UserApi[]> {
        let params = [];

        if (search) {
            params.push(`search=${encodeURIComponent(search)}`);
        }

        const paramsStr = params ? '?' + params.join('&') : '';

        let response = await fetch(
            `/admin/wagtail_review/api/users/${paramsStr}`,
            {
                credentials: 'same-origin'
            }
        );

        return response.json();
    }

    async _newReviwer(body: string): Promise<NewReviewerResponse> {
        let response = await fetch(`/admin/wagtail_review/api/reviewers/`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json'
            },
            body
        });

        if (response.status === 200 || response.status === 201) {
            return {
                status: 'ok',
                reviewer: await response.json()
            };
        } else if (response.status == 400) {
            return {
                status: 'error',
                ...(await response.json())
            };
        } else {
            throw new Error(
                `reviewer api returned unexpected status code: ${response.status}`
            );
        }
    }

    async newInternalReviewer(
        user_id: number | string
    ): Promise<NewReviewerResponse> {
        return this._newReviwer(
            JSON.stringify({
                user_id
            })
        );
    }

    async newExternalReviewer(email: string): Promise<NewReviewerResponse> {
        return this._newReviwer(
            JSON.stringify({
                email
            })
        );
    }
}
