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
        let onClickCloseButton = () => {
            this.props.store.dispatch(hideShareModal());
        };

        let onKeyDownInEmailBox = async (
            e: React.KeyboardEvent<HTMLInputElement>
        ) => {
            if (e.key == 'Enter') {
                let target = e.target;
                if (target instanceof HTMLInputElement) {
                    let newEmail = target.value;

                    this.setState({ errors: null });

                    let response = await this.props.api.newShare(newEmail);

                    if (response.status == 'ok') {
                        target.value = '';
                        this.props.store.dispatch(
                            putShare(Share.fromApi(response.share))
                        );
                    } else {
                        this.setState({ errors: response });
                    }
                }
            }
        };

        let renderedShares = this.props.shares.map(share => {
            return (
                <tr>
                    <td>{share.email}</td>
                    <td>
                        {!share.accessedAt
                            ? 'Never'
                            : dateFormat(share.accessedAt)}
                    </td>
                    <td>{!share.accessedAt
                            ? 'Never'
                            : dateFormat(share.expiresAt)}</td>
                </tr>
            );
        });

        let error = <></>;
        if (this.state.errors && this.state.errors['email']) {
            error = <div className="error">{this.state.errors['email']}</div>;
        }

        return (
            <WagtailReactModal
                isOpen={this.props.isShareModalOpen}
                contentLabel="Share"
                onClickCloseButton={onClickCloseButton}
            >
                <div className="nice-padding">
                    <p></p>
                    <input
                        type="text"
                        placeholder="Enter email address"
                        onKeyDown={onKeyDownInEmailBox}
                    ></input>
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
