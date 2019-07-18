import { Store } from 'redux';

import * as actions from '../actions/share';
import { ShareApi } from '../api';

export class Share {
    id: number;
    email: string;
    accessedAt: number | null;
    expiresAt: number | null;

    constructor(
        id: number,
        email: string,
        accessedAt: number,
        expiresAt: number
    ) {
        this.id = id;
        this.email = email;
        this.accessedAt = accessedAt;
        this.expiresAt = expiresAt;
    }

    static fromApi(data: ShareApi): Share {
        return new Share(
            data.id,
            data.user.email,
            data.last_accessed_at ? Date.parse(data.last_accessed_at) : null,
            data.expires_at ? Date.parse(data.expires_at) : null
        );
    }
}

export interface State {
    shares: Share[];
    isShareModalOpen: boolean;
}

function initialState(): State {
    return {
        shares: [],
        isShareModalOpen: false
    };
}

export function reducer(state: State | undefined, action: actions.Action) {
    if (typeof state === 'undefined') {
        state = initialState();
    }

    switch (action.type) {
        case actions.SHOW_HIDE_SHARE_MODAL: {
            state = Object.assign({}, state, { isShareModalOpen: action.show });
            break;
        }

        case actions.PUT_SHARE: {
            let shareIndex = null;
            for (let i in state.shares) {
                let share = state.shares[i];
                if (share.id == action.share.id) {
                    shareIndex = i;
                    break;
                }
            }

            let newShares = state.shares.slice();

            if (shareIndex == null) {
                newShares.push(action.share);
            } else {
                newShares[parseInt(shareIndex)] = action.share;
            }

            state = Object.assign({}, state, { shares: newShares });

            break;
        }

        case actions.DELETE_SHARE: {
            let shareIndex = null;
            for (let i in state.shares) {
                let share = state.shares[i];
                if (share.id == action.shareId) {
                    shareIndex = i;
                    break;
                }
            }

            if (shareIndex != null) {
                let newShares = state.shares.slice();
                newShares.splice(parseInt(shareIndex), 1);
                state = Object.assign({}, state, { shares: newShares });
            }

            break;
        }
    }

    console.log(action);

    return state;
}

export type Store = Store<State, actions.Action>;
