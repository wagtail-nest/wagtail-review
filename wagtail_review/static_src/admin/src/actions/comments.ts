import { Comment } from '../state/comments';

export const LOAD_COMMENTS = 'load-comments';
export const SHOW_HIDE_COMMENTS = 'show-hide-comments';
export const SHOW_HIDE_RESOLVED_COMMENTS = 'show-hide-resolved-comments';

interface LoadCommentsAction {
    type: 'load-comments';
    comments: Comment[];
}

interface ShowHideCommentsAction {
    type: 'show-hide-comments';
    show: boolean;
}

interface ShowHideResolvedCommentsAction {
    type: 'show-hide-resolved-comments';
    show: boolean;
}

export type Action = LoadCommentsAction | ShowHideCommentsAction | ShowHideResolvedCommentsAction;

export function loadComments(comments: Comment[]): LoadCommentsAction {
    return {
        type: LOAD_COMMENTS,
        comments
    };
}

export function showComments(): ShowHideCommentsAction {
    return {
        type: SHOW_HIDE_COMMENTS,
        show: true
    };
}

export function hideComments(): ShowHideCommentsAction {
    return {
        type: SHOW_HIDE_COMMENTS,
        show: false
    };
}

export function showHideResolvedComments(show: boolean): ShowHideResolvedCommentsAction {
    return {
        type: SHOW_HIDE_RESOLVED_COMMENTS,
        show
    };
}
