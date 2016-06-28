import {div, label, input, p, form, span, h2} from '@cycle/dom';
import {Observable} from 'rx';
//import dialog from 'dialog';
//import {dialog} from 'electron';
//const electron = require('electron');

import i_styles from './input.css';
import c_styles from './common.css';
let styles = {};
Object.assign(styles, i_styles, c_styles);


//var remote = require('remote');
import remote from 'remote';
var dialog = remote.require('electron').dialog;


const showDialog = Observable.fromCallback(dialog.showOpenDialog);


function intent(DOM, id){

    const newValue$ = DOM.select(`#${id}`).events('click')
    .flatMap(() => showDialog({properties: ['openDirectory'] }))
    .map(dirs => (dirs === undefined ? '' : dirs[0]) )
    .share()
    ;



    return newValue$;
}

function model(newValue$, initialValue){

    return newValue$.startWith(initialValue);
    //return newValue$.startWith(undefined);

}

//function view(state$, isFocus$, id, labelName){
function view(state$, id, labelName){

    //const vtree$ = Observable.combineLatest(state$, isFocus$,
    const vtree$ =  state$.map(
    //const vtree$ =  Observable.just('').map(

            //( value, focus ) =>
            ( value ) =>

            div({className: styles.group},
                [
                    input({id, required: true, className: styles.input, value}),
                    span({className: styles.bar}),
                    label({for: id, className: ( value ? styles.labelActive : styles.labelInactive)}, labelName),
                ])
            );

    return vtree$;
}


function InputFile({DOM, props}){

    //const id$ = props$.pluck('id').first();
    //const label$ = props$.pluck('label').first();
    //const initialValue$ = props$
    //  .map(props => (props.initialValue ? props.initialValue : '' ))
    //  .first();
    const {id, labelName} = props;
    const initialValue = props.initialValue ? props.initialValue : '';

    //const {newValue$, isFocus$} = intent(DOM, id);
    const newValue$ = intent(DOM, id);
    const state$ = model(newValue$, initialValue);
    //const vtree$ = view(state$, isFocus$, id, labelName);
    const vtree$ = view(state$, id, labelName);


  return {
      vtree$,
      value$: state$,
      id
  }


}

export default InputFile;
