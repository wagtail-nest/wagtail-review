import { Share } from '../state/share';

export const SHOW_HIDE_SHARE_MODAL = 'show-hide-share-modal';
export const PUT_SHARE = 'put-share';
export const DELETE_SHARE = 'delete-share';

interface ShowHideShareModalAction {
    type: 'show-hide-share-modal';
    show: boolean;
}

interface PutShareAction {
    type: 'put-share';
    share: Share;
}

interface DeleteShareAction {
    type: 'delete-share';
    shareId: number;
}

export type Action =
    | ShowHideShareModalAction
    | PutShareAction
    | DeleteShareAction;

export function showShareModal(): ShowHideShareModalAction {
    return {
        type: SHOW_HIDE_SHARE_MODAL,
        show: true
    };
}

export function hideShareModal(): ShowHideShareModalAction {
    return {
        type: SHOW_HIDE_SHARE_MODAL,
        show: false
    };
}

export function putShare(share: Share): PutShareAction {
    return {
        type: PUT_SHARE,
        share
    };
}

export function deleteShare(shareId: number): DeleteShareAction {
    return {
        type: DELETE_SHARE,
        shareId
    };
}
