// @flow
import type { State } from './state';
import { getNewExperiment, getNewExperimentErrors, getNewProject, getNewProjectErrors } from './selectors';

export type Action
    = {| type: 'NEWPROJECT_INIT' |}
    | {| type: 'NEWPROJECT_CHANGE', field: string, value: string |}
    | {| type: 'NEWPROJECT_SUBMIT' |}
    | {| type: 'NEWPROJECT_CLEAR' |}
    | {| type: 'PROJECTS_ADD', id: string, name: string, description: string |}
    | {| type: 'NEWEXPERIMENT_INIT', projectId: string |}
    | {| type: 'NEWEXPERIMENT_CHANGE', field: 'name'|'description'|'scannerId', value: string |}
    | {| type: 'NEWEXPERIMENT_CHANGE', field: 'duration'|'interval', value: number |}
    | {| type: 'NEWEXPERIMENT_CHANGE', field: 'pinning', value: Array<string> |}
    | {| type: 'NEWEXPERIMENT_SUBMIT' |}
    | {| type: 'NEWEXPERIMENT_CLEAR' |}
    | {|
        type: 'EXPERIMENTS_ADD',
        description: string,
        duration: number,
        id: string,
        interval: number,
        name: string,
        projectId: string,
        scannerId: string,
        pinning: Array<string>,
    |}
    | {| type: 'EXPERIMENTS_START', id: string, date: Date |}
    | {| type: 'EXPERIMENTS_STOP', id: string, reason: string, date: Date |}
    | {| type: 'EXPERIMENTS_REMOVE', id: string |}
    | {| type: 'EXPERIMENTS_FEATUREEXTRACT', id: string, keepQC: boolean |}
    | {| type: 'EXPERIMENTS_DONE', id: string |}
    | {| type: 'EXPERIMENTS_REOPEN', id: string |}

export function initNewProject(): Action {
    return { type: 'NEWPROJECT_INIT' };
}

export function changeNewProject(field: string, value: string): Action {
    return { type: 'NEWPROJECT_CHANGE', field, value };
}

export function clearNewProject(): Action {
    return { type: 'NEWPROJECT_CLEAR' };
}

export function addProject(name: string, description: string): Action {
    return {
        type: 'PROJECTS_ADD',
        name,
        description,
        id: new Date().getTime().toString(),
    };
}

export function initNewExperiment(projectId: string): Action {
    return { type: 'NEWEXPERIMENT_INIT', projectId };
}

export function changeNewExperiment(field: string, value: string|number|Array<string>): Action {
    switch (field) {
    case 'description':
    case 'name':
    case 'scannerId':
        if (typeof value !== 'string') {
            throw TypeError(`Invalid type ${typeof (value)} for field ${field}`);
        }
        return {
            type: 'NEWEXPERIMENT_CHANGE',
            field,
            value: (value: string),
        };
    case 'duration':
    case 'interval':
        if (typeof value === 'number') {
            return {
                type: 'NEWEXPERIMENT_CHANGE',
                field,
                value: (value: number),
            };
        }
        throw TypeError(`Invalid type ${typeof (value)} for field ${field}`);
    case 'pinning':
        if (typeof value === 'object') {
            return {
                type: 'NEWEXPERIMENT_CHANGE',
                field,
                value: (value: Array<string>),
            };
        }
        throw TypeError(`Invalid type ${typeof (value)} for field ${field}`);
    default:
        throw Error(`Unknown field ${field}`);
    }
}

export function clearNewExperiment(): Action {
    return {
        type: 'NEWEXPERIMENT_CLEAR',
    };
}

export function addExperiment(
    projectId: string,
    name: string,
    description: string,
    duration: number,
    interval: number,
    scannerId: string,
    pinning: Array<string>,
): Action {
    return {
        type: 'EXPERIMENTS_ADD',
        id: new Date().getTime().toString(),
        projectId,
        name,
        description,
        duration,
        interval,
        scannerId,
        pinning,
    };
}

export function startExperiment(id: string): Action {
    return {
        type: 'EXPERIMENTS_START',
        id,
        date: new Date(),
    };
}

export function stopExperiment(id: string, reason: string): Action {
    return {
        type: 'EXPERIMENTS_STOP',
        id,
        reason,
        date: new Date(),
    };
}

export function removeExperiment(id: string): Action {
    return {
        type: 'EXPERIMENTS_REMOVE',
        id,
    };
}

export function doneExperiment(id: string) : Action {
    return {
        type: 'EXPERIMENTS_DONE',
        id,
    };
}

export function reopenExperiment(id: string) : Action {
    return {
        type: 'EXPERIMENTS_REOPEN',
        id,
    };
}

type ThunkAction = (dispatch: Action => any, getState: () => State) => any;

export function submitNewProject(): ThunkAction {
    return (dispatch, getState) => {
        const newProject = getNewProject(getState());
        if (newProject == null) return;
        dispatch({ type: 'NEWPROJECT_SUBMIT' });
        const errors = getNewProjectErrors(getState());
        if (errors.size > 0) return;
        dispatch(addProject(newProject.name, newProject.description));
        dispatch(clearNewProject());
    };
}

export function submitNewExperiment(): ThunkAction {
    return (dispatch, getState) => {
        dispatch({ type: 'NEWEXPERIMENT_SUBMIT' });
        const newExperiment = getNewExperiment(getState());
        if (newExperiment == null) return;
        const errors = getNewExperimentErrors(getState());
        if (errors.size > 0) return;
        dispatch(addExperiment(
            newExperiment.projectId,
            newExperiment.name,
            newExperiment.description,
            newExperiment.duration,
            newExperiment.interval,
            newExperiment.scannerId,
            newExperiment.pinning,
        ));
        dispatch(clearNewExperiment());
    };
}

export function featureExtract(id: string, keepQC: boolean): ThunkAction {
    return (dispatch, getState) => {
        // This is a stub since API-calls are not yet impleme3nted
    };
};
