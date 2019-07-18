import * as React from 'react';
import * as Modal from 'react-modal';

import './style.scss';

interface Props extends Modal.Props {
    onClickCloseButton?(): void;
}

export default class WagtailReactModal extends React.Component<Props> {
    render() {
        let onClickClose = (e: React.MouseEvent) => {
            e.preventDefault();

            if (this.props.onClickCloseButton) {
                this.props.onClickCloseButton();
            }
        };

        let defaultProps = {
            className: 'react-modal__dialog',
            overlayClassName: 'react-modal'
        };

        let props: Modal.Props = Object.assign(defaultProps, this.props);

        let oldOnAfterOpen = props.onAfterOpen;
        props.onAfterOpen = () => {
            let backdrop = document.body.appendChild(
                document.createElement('div')
            );
            backdrop.classList.add('js-wagtail-react-modal-backdrop');
            backdrop.classList.add('modal-backdrop');
            backdrop.classList.add('in');

            if (oldOnAfterOpen) {
                oldOnAfterOpen();
            }
        };

        let oldOnAfterClose = props.onAfterClose;
        props.onAfterClose = () => {
            let backdrop = document.querySelector(
                'body > div.js-wagtail-react-modal-backdrop'
            );

            if (backdrop instanceof HTMLElement) {
                backdrop.remove();
            }

            if (oldOnAfterClose) {
                oldOnAfterClose();
            }
        };

        return (
            <Modal {...props}>
                <div className="react-modal__content">
                    <button
                        type="button"
                        className="button close icon text-replace icon-cross"
                        data-dismiss="modal"
                        aria-hidden="true"
                        onClick={onClickClose}
                    >
                        ×
                    </button>
                    <div className="react-modal__body">
                        <header className="merged tab-merged">
                            <div className="row nice-padding">
                                <div className="left">
                                    <div className="col header-title">
                                        <h1 className="icon icon-share">
                                            {this.props.contentLabel}
                                        </h1>
                                    </div>
                                </div>
                            </div>
                        </header>

                        <div className="tab-content">{this.props.children}</div>
                    </div>
                </div>
            </Modal>
        );
    }

    componentDidMount() {
        Modal.setAppElement('div.wrapper');
    }
}
