function createTab(text: string, id: string|undefined, onClick: (e: MouseEvent) => void) {
    const liElement = document.createElement('li');

    if (id) {
        liElement.id = id;
    }

    const aElement = liElement.appendChild(document.createElement('a'));
    aElement.href = '#';
    aElement.addEventListener(
        'click',
        e => {
            e.preventDefault();
            e.stopPropagation();
            onClick(e);
        },
        { capture: true }
    );
    aElement.appendChild(document.createTextNode(text));

    return liElement;
}

interface TabConfig {
    text: string;
    id?: string;
    onClick: () => void;
}

export function initTabs(tabs: TabConfig[]) {
    const tabsElement = document.querySelector('ul.tab-nav');
    if (!(tabsElement instanceof HTMLUListElement)) {
        console.error('[review] Cannot locate tabs element in DOM');
        return;
    }
    tabsElement.style.position = 'relative';

    const container = document.createElement('div');
    container.style.position = 'absolute';
    container.style.right = '50px';

    for (const tab of tabs) {
        container.appendChild(createTab(tab.text, tab.id, tab.onClick));
    }

    tabsElement.appendChild(container);
}
