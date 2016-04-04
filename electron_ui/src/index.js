import {Observable} from 'rx';
import Cycle from '@cycle/core';
import {makeDOMDriver, div, label, input, p, form, span, h2} from '@cycle/dom';

import styles from './index.css';

import Select from './components/selector.js'
import Input from './components/input.js'


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


  const props$ = Observable.just({options: ['X-Files', 'Fargo', 'True Detective'], initial: 'Fargo'});
  const select = Select({DOM: drivers.DOM, props$})
  const selectVTree$ = select.DOM;


  function makeInput(id, labelName, initialValue){
      return Input({DOM: drivers.DOM,
                    props: {id, labelName, initialValue}
      });
  }

  const nameInput = makeInput('name', 'User name');
  const emailInput = makeInput('email', 'User email');
  //const projectNameInput = makeInput('project_name', 'Project name'),
  //const directoryInput = makeInput('directory', 'Directory'),
  //const licenseInput = makeInput('license', 'License'),
  //const commitInput = makeInput('commit', 'Initial commit'),

  return {

    DOM: Observable.combineLatest(nameInput.value$, emailInput.value$, selectVTree$, select.value$, nameInput.vtree$, emailInput.vtree$,
                                (name, email, selectVTree, selectValue, nameInputVTree, emailInputVTree) => {

        return div({className: styles.container}, [
            form([
                nameInputVTree,
                emailInputVTree,
                //newInput('name', 'User name'),
                //newInput('email', 'User email'),
                //newInput('project_name', 'Project name'),
                //newInput('directory', 'Directory'),
                //newInput('license', 'License'),
                //newInput('commit', 'Initial commit'),
                selectVTree,
            ]),
            //h2(`${name} <${email}> with value ${selectValue}`)
            h2(`${name} <${email}> with value ${selectValue}`)
            ]);

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
