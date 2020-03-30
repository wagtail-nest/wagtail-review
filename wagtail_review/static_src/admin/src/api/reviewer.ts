export interface UserApi {
    id: number | string;
    name: string;
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
    csrfToken: string;
    usersUrl: string;
    reviewerUrl: string;
    csrfHeaderName: string;

    constructor(csrfToken: string, usersUrl: string, reviewerUrl: string, csrfHeaderName: string) {
        this.csrfToken = csrfToken;
        this.usersUrl = usersUrl;
        this.reviewerUrl = reviewerUrl;
        this.csrfHeaderName = csrfHeaderName;
    }

    async getUsers({ search }: { search?: string }): Promise<UserApi[]> {
        let params = [];

        if (search) {
            params.push(`search=${encodeURIComponent(search)}`);
        }

        const paramsStr = params ? '?' + params.join('&') : '';

        let response = await fetch(
            `${this.usersUrl}${paramsStr}`,
            {
                credentials: 'same-origin'
            }
        );

        return response.json();
    }

    async _newReviewer(body: string): Promise<NewReviewerResponse> {
        let response = await fetch(this.reviewerUrl, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                [this.csrfHeaderName]: this.csrfToken
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
        return this._newReviewer(
            JSON.stringify({
                user_id
            })
        );
    }

    async newExternalReviewer(email: string): Promise<NewReviewerResponse> {
        return this._newReviewer(
            JSON.stringify({
                email
            })
        );
    }
}
