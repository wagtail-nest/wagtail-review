import * as React from 'react';
import * as Autocomplete from 'react-autocomplete';

import ReviewerAPIClient, {
    NewReviewerValidationError,
    UserApi,
    NewReviewerResponse
} from '../../api/reviewer';
import { Store, State, Reviewer } from '../../state/reviewer-chooser';
import { putReviewer, deleteReviewer } from '../../actions/reviewer-chooser';

import './style.scss';

function isValidEmail(email: string) {
    var re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email.toLowerCase());
}

interface ReviewersChooserProps extends State {
    api: ReviewerAPIClient;
    store: Store;
    inputName: string;
}

interface ReviewersChooserState {
    autocompleteSearch: string;
    autocompleteResults: UserApi[];
    errors: NewReviewerValidationError | null;
}

export default class ReviewerChooser extends React.Component<
    ReviewersChooserProps,
    ReviewersChooserState
> {
    constructor(props: ReviewersChooserProps) {
        super(props);

        this.state = {
            autocompleteSearch: '',
            autocompleteResults: [],
            errors: null
        };
    }

    render() {
        const { api, store, reviewers } = this.props;

        const onKeyDownInEmailBox = async (
            e: React.KeyboardEvent<HTMLInputElement>
        ) => {
            if (e.key === 'Enter') {
                e.preventDefault();

                const newEmail = this.state.autocompleteSearch;

                if (isValidEmail(newEmail)) {
                    this.setState({ errors: null });

                    const response = await api.newExternalReviewer(newEmail);

                    if (response.status === 'ok') {
                        this.setState({
                            autocompleteSearch: '',
                            autocompleteResults: []
                        });
                        store.dispatch(
                            putReviewer(Reviewer.fromApi(response.reviewer))
                        );
                    } else {
                        this.setState({ errors: response });
                    }
                }
            }
        };

        const renderedReviewers = reviewers.map(reviewer => {
            const onClickRemove = (e: React.MouseEvent<HTMLButtonElement>) => {
                e.preventDefault();

                store.dispatch(deleteReviewer(reviewer.id));
            };

            return (
                <tr>
                    <td>
                        {reviewer.display()}

                        <input
                            type="hidden"
                            name={this.props.inputName}
                            value={reviewer.id}
                        />

                        <button
                            className="reviewer-chooser__remove-button button icon text-replace white icon-bin hover-no"
                            onClick={onClickRemove}
                        >
                            Remove
                        </button>
                    </td>
                </tr>
            );
        });

        const { errors } = this.state;
        let error = <></>;
        if (errors && errors.email) {
            error = <div className="error">{errors.email}</div>;
        }

        let items: (
            | UserApi
            | 'email')[] = this.state.autocompleteResults.slice();

        if (isValidEmail(this.state.autocompleteSearch)) {
            items.unshift('email');
        }

        return (
            <div className="reviewer-chooser">
                <Autocomplete
                    items={items}
                    value={this.state.autocompleteSearch}
                    onChange={async e => {
                        this.setState({ autocompleteSearch: e.target.value });

                        if (e.target.value) {
                            const response = await api.getUsers({
                                search: e.target.value
                            });
                            this.setState({ autocompleteResults: response });
                        } else {
                            this.setState({ autocompleteResults: [] });
                        }
                    }}
                    getItemValue={result => {
                        if (result === 'email') {
                            return 'email';
                        } else {
                            return result.id.toString();
                        }
                    }}
                    renderItem={(result: UserApi | 'email', isHighlighted) => {
                        const classes = [
                            'reviewer-chooser__autocomplete-option'
                        ];
                        if (isHighlighted) {
                            classes.push(
                                'reviewer-chooser__autocomplete-option--highlighted'
                            );
                        }

                        if (result === 'email') {
                            return (
                                <div className={classes.join(' ')}>
                                    Email address:{' '}
                                    {this.state.autocompleteSearch}
                                </div>
                            );
                        } else {
                            return (
                                <div className={classes.join(' ')}>
                                    {result.username}
                                </div>
                            );
                        }
                    }}
                    onSelect={async userId => {
                        this.setState({ errors: null });

                        let response: NewReviewerResponse;
                        if (userId === 'email') {
                            response = await api.newExternalReviewer(
                                this.state.autocompleteSearch
                            );
                        } else {
                            response = await api.newInternalReviewer(userId);
                        }

                        if (response.status === 'ok') {
                            this.setState({
                                autocompleteSearch: '',
                                autocompleteResults: []
                            });
                            store.dispatch(
                                putReviewer(Reviewer.fromApi(response.reviewer))
                            );
                        } else {
                            this.setState({ errors: response });
                        }
                    }}
                    inputProps={{
                        placeholder: 'Enter username or email address',
                        onKeyDown: onKeyDownInEmailBox
                    }}
                    // Remove default `display: 'inline-block';` style
                    wrapperStyle={{}}
                />

                {error}

                <table className="listing">
                    <tbody>{renderedReviewers}</tbody>
                </table>
            </div>
        );
    }
}
