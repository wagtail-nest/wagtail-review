import { Store } from 'redux';

import * as actions from '../actions/comments';
import { CommentApi, CommentReplyApi } from '../api';

export class Author {
    name: string;

    constructor(name: string) {
        this.name = name;
    }

    static unknown(): Author {
        return new Author('Unknown');
    }

    static fromApi(data: any): Author {
        return new Author(data.name);
    }
}

export type CommentReplyMode =
    | 'default'
    | 'editing'
    | 'saving'
    | 'delete_confirm'
    | 'deleting'
    | 'deleted'
    | 'save_error'
    | 'delete_error';

export class CommentReply {
    id: number;

    author: Author;

    date: number;

    text: string;

    constructor(id: number, author: Author, date: number, text: string) {
        this.id = id;
        this.author = author;
        this.date = date;
        this.text = text;
    }

    static fromApi(data: CommentReplyApi): CommentReply {
        return new CommentReply(
            data.id,
            new Author(data.author.name),
            Date.parse(data.created_at),
            data.text
        );
    }
}

export class Comment {
    id: number;

    isResolved: boolean;

    author: Author;

    date: number;

    text: string;

    replies: CommentReply[];

    frontendUrl: string;

    constructor(
        id: number,
        isResolved: boolean,
        author: Author,
        date: number,
        text: string,
        replies: CommentReply[],
        frontendUrl: string,
    ) {
        this.id = id;
        this.isResolved = isResolved;
        this.author = author;
        this.date = date;
        this.text = text;
        this.replies = replies;
        this.frontendUrl = frontendUrl;
    }

    static fromApi(data: CommentApi): Comment {
        return new Comment(
            data.id,
            data.is_resolved,
            new Author(data.author.name),
            Date.parse(data.created_at),
            data.text,
            data.replies.map(CommentReply.fromApi),
            data.frontend_url,
        );
    }
}

export interface State {
    isOpen: boolean;
    comments: Comment[];
    showResolvedComments: boolean;
}

function initialState(): State {
    return {
        isOpen: false,
        comments: [],
        showResolvedComments: false,
    };
}

export function reducer(state: State | undefined, action: actions.Action) {
    if (typeof state === 'undefined') {
        state = initialState();
    }

    switch (action.type) {
        case actions.LOAD_COMMENTS: {
            state = Object.assign({}, state, { comments: action.comments });
            break;
        }
        case actions.SHOW_HIDE_COMMENTS: {
            state = Object.assign({}, state, { isOpen: action.show });
            break;
        }
        case actions.SHOW_HIDE_RESOLVED_COMMENTS: {
            state = Object.assign({}, state, { showResolvedComments: action.show });
            break;
        }
    }

    return state;
}

export type Store = Store<State, actions.Action>;
