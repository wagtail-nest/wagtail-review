export interface UserApi {
    email: string;
}

export interface ShareApi {
    id: number;
    user: UserApi;
    shared_by: string;
    shared_at: string;
    first_accessed_at: string | null;
    last_accessed_at: string | null;
    expires_at: string;
}

export interface NewShareSuccess {
    status: 'ok';
    share: ShareApi;
}

export interface NewShareValidationError {
    status: 'error';
    email?: string;
}

export type NewShareResponse = NewShareSuccess | NewShareValidationError;

export interface ReviewerApi {
    name: string;
}

export interface CommentReplyApi {
    id: number;
    author: ReviewerApi;
    text: string;
    created_at: string;
    updated_at: string;
}

export interface CommentApi {
    id: number;
    author: ReviewerApi;
    quote: string;
    text: string;
    created_at: string;
    updated_at: string;
    is_resolved: boolean;
    replies: CommentReplyApi[];
    frontend_url: string;
}

export default class PageAPIClient {
    pageId: number;
    csrfToken: string;
    sharesUrl: string;
    commentsUrl: string;

    constructor(pageId: number, csrfToken: string, sharesUrl: string, commentsUrl: string) {
        this.pageId = pageId;
        this.csrfToken = csrfToken;
        this.sharesUrl = sharesUrl;
        this.commentsUrl = commentsUrl;
    }

    async getShares(): Promise<ShareApi[]> {
        let response = await fetch(
            this.sharesUrl,
            {
                credentials: 'same-origin'
            }
        );

        return response.json();
    }

    async newShare(email: string): Promise<NewShareResponse> {
        let response = await fetch(
            this.sharesUrl,
            {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    email
                })
            }
        );

        if (response.status == 201) {
            return {
                status: 'ok',
                share: await response.json()
            };
        } else if (response.status == 400) {
            return {
                status: 'error',
                ...(await response.json())
            };
        } else {
            throw new Error(
                `share api returned unexpected status code: ${response.status}`
            );
        }
    }

    async getComments(): Promise<CommentApi[]> {
        let response = await fetch(
            this.commentsUrl,
            {
                credentials: 'same-origin'
            }
        );

        return response.json();
    }
}
