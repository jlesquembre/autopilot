import {Observable} from 'rx';
import Cycle from '@cycle/core';
import {makeDOMDriver, div, label, input, p, form, span, h2} from '@cycle/dom';

import styles from './index.css';

import Select from './components/selector.js'
import Input from './components/input.js'
import InputFile from './components/inputFile.js'

// Include normalize.css
import normalize from 'normalize.css/normalize.css';
//require('normalize.css/normalize.css');

//import {restart, restartable} from 'cycle-restart';

//function getInputValueObservable(DOM, id){
//    return DOM.select(id).events('input').map(ev => ev.target.value).startWith('');
//}
//
//function newInput(id, labelText){
//    return div({className: styles.group},
//        [
//            input({id, required: true, className: styles.input}),
//            span({className: styles.bar}),
//            label({for: id, className: styles.label}, labelText),
//        ]);
//}


function main(drivers) {
  //let [name$, email$] = ['#name', '#email'].map(id => getInputValueObservable(drivers.DOM, id) );


  const props$ = Observable.just({options: ['GPLv2', 'GPLv3', 'MIT'], initial: 'GPLv2', labelName: 'License'});
  const licenseSelect = Select({DOM: drivers.DOM, props$})


  function makeInput(id, labelName, initialValue){
      return Input({DOM: drivers.DOM,
                    props: {id, labelName, initialValue}
      });
  }

  const nameInput = makeInput('name', 'User name');
  const emailInput = makeInput('email', 'User email');
  const projectNameInput = makeInput('project_name', 'Project name');
  //const directoryInput = makeInput('directory', 'Directory'),
  const directoryInput = InputFile({DOM: drivers.DOM, props: {id: 'directory', labelName: 'Directory'} });
  //const commitInput = makeInput('commit', 'Initial commit'),

  return {

    DOM: Observable.combineLatest(nameInput.value$, emailInput.value$, projectNameInput.value$, licenseSelect.value$, directoryInput.value$,
                                  nameInput.vtree$, emailInput.vtree$, projectNameInput.vtree$, licenseSelect.vtree$, directoryInput.vtree$,
                                (name, email, projectName, license, directory,
                                 nameInputVTree, emailInputVTree, projectNameInputVTree, licenseSelectVTree, directoryInputVTree) => {

        return div({className: styles.container}, div({className: styles.centeredItem}, [
            form([
                nameInputVTree,
                emailInputVTree,
                projectNameInputVTree,
                //input({type:'file', webkitdirectory: true}),
                directoryInputVTree,
                licenseSelectVTree,
                //initialCommitVTree,
            ]),
            h2(`${name} <${email}> with value ${license}`)
            ]));

        }

    ),


  };
}

const drivers = {
  DOM: makeDOMDriver('#app')
  //DOM: restartable(makeDOMDriver('#app'))
};

Cycle.run(main, drivers);

//if (module.hot) {
//  module.hot.accept('./src/app', () => {
//    app = require('./src/app').default;
//
//    restart(app, drivers, {sinks, sources});
//  });
//}
