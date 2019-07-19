import * as React from 'react';
import * as dateFormat from 'dateformat';

import APIClient, { NewShareValidationError } from '../../api';
import { Store, State, Share } from '../../state/share';
import { hideShareModal, putShare } from '../../actions/share';

import WagtailReactModal from '../WagtailReactModal';

import './style.scss';

interface ShareModalProps extends State {
    api: APIClient;
    store: Store;
}

interface ShareModalState {
    errors: NewShareValidationError | null;
}

export default class ShareModal extends React.Component<
ShareModalProps,
ShareModalState
> {
    constructor(props: ShareModalProps) {
        super(props);

        this.state = {
            errors: null
        };
    }

    render() {
        const { api, store, isShareModalOpen, shares } = this.props;

        const onClickCloseButton = () => {
            store.dispatch(hideShareModal());
        };

        const onKeyDownInEmailBox = async (
            e: React.KeyboardEvent<HTMLInputElement>
        ) => {
            if (e.key === 'Enter') {
                const {target} = e;
                if (target instanceof HTMLInputElement) {
                    const newEmail = target.value;

                    this.setState({ errors: null });

                    const response = await api.newShare(newEmail);

                    if (response.status === 'ok') {
                        target.value = '';
                        store.dispatch(
                            putShare(Share.fromApi(response.share))
                        );
                    } else {
                        this.setState({ errors: response });
                    }
                }
            }
        };

        const renderedShares = shares.map(share => {
            return (
                <tr>
                    <td>{share.email}</td>
                    <td>
                        {share.accessedAt
                        ? dateFormat(share.accessedAt)
                        : 'Never'}
                    </td>
                    <td>
                        {share.expiresAt
                            ? dateFormat(share.expiresAt)
                            : 'Never'}
                    </td>
                </tr>
            );
        });

        const { errors } = this.state;
        let error = <></>;
        if (errors && errors.email) {
            error = <div className="error">{errors.email}</div>;
        }

        return (
            <WagtailReactModal
                isOpen={isShareModalOpen}
                contentLabel="Share"
                onClickCloseButton={onClickCloseButton}
            >
                <div className="nice-padding">
                    <p />
                    <input
                        type="text"
                        placeholder="Enter email address"
                        onKeyDown={onKeyDownInEmailBox}
                    />
                    {error}

                    <table>
                        <thead>
                            <th>Email</th>
                            <th>Last opened</th>
                            <th>Expires at</th>
                        </thead>
                        <tbody>{renderedShares}</tbody>
                    </table>
                </div>
            </WagtailReactModal>
        );
    }
}
