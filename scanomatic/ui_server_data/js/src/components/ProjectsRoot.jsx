import React from 'react';
import PropTypes from 'prop-types';

import myTypes from '../prop-types';
import ProjectPanel from './ProjectPanel';
import ExperimentPanel from './ExperimentPanel';
import NewProjectPanel from './NewProjectPanel';
import NewExperimentPanel from './NewExperimentPanel';

export default class ProjectsRoot extends React.Component {
    renderProject(project, defaultExpanded) {
        const {
            onNewExperiment, newExperiment, newExperimentErrors, newExperimentActions,
            scanners, experimentActions,
        } = this.props;
        const hasNewExperiment = newExperiment && newExperiment.projectId === project.id;
        return (
            <ProjectPanel
                {...project}
                key={project.name}
                onNewExperiment={() => onNewExperiment(project.id)}
                newExperimentDisabled={hasNewExperiment}
                scanners={scanners}
                defaultExpanded={defaultExpanded}
            >
                {hasNewExperiment &&
                <NewExperimentPanel
                    {...newExperiment}
                    {...newExperimentActions}
                    projectName={project.name}
                    errors={newExperimentErrors}
                    scanners={scanners}
                />}
                {project.experiments.map((experiment, eIdx) => (
                    <ExperimentPanel
                        key={experiment.id}
                        {...experiment}
                        {...experimentActions}
                        defaultExpanded={eIdx === 0}
                    />
                ))}
            </ProjectPanel>);
    }

    render() {
        const {
            projects, newProject, newProjectActions, newProjectErrors, onNewProject,
        } = this.props;
        let newProjectForm = null;
        if (newProject) {
            newProjectForm = (<NewProjectPanel
                {...newProject}
                {...newProjectActions}
                errors={newProjectErrors}
            />);
        }
        const newProjectButton = (
            <button className="btn btn-primary new-project" onClick={onNewProject} disabled={newProject}>
                <div className="glyphicon glyphicon-plus" /> New Project
            </button>
        );

        return (
            <div>
                <h1>Projects</h1>
                {newProjectButton}
                {newProjectForm}
                {projects.map((p, pIdx) => this.renderProject(p, pIdx === 0))}
            </div>
        );
    }
}

ProjectsRoot.propTypes = {
    newExperiment: PropTypes.shape(myTypes.experimentShape),
    newExperimentActions: PropTypes.shape({
        onChange: PropTypes.func.isRequired,
        onCancel: PropTypes.func.isRequired,
        onSubmit: PropTypes.func.isRequired,
    }).isRequired,
    newExperimentErrors: PropTypes.instanceOf(Map),
    newProject: PropTypes.shape(myTypes.projectShape),
    newProjectActions: PropTypes.shape({
        onChange: PropTypes.func.isRequired,
        onCancel: PropTypes.func.isRequired,
        onSubmit: PropTypes.func.isRequired,
    }).isRequired,
    experimentActions: PropTypes.shape({
        onStart: PropTypes.func.isRequired,
        onRemove: PropTypes.func.isRequired,
        onStop: PropTypes.func.isRequired,
        onDone: PropTypes.func.isRequired,
        onReopen: PropTypes.func.isRequired,
        onFeatureExtract: PropTypes.func.isRequired,
    }).isRequired,
    newProjectErrors: PropTypes.instanceOf(Map),
    onNewExperiment: PropTypes.func.isRequired,
    onNewProject: PropTypes.func.isRequired,
    projects: PropTypes.arrayOf(PropTypes.shape(myTypes.projectShape)),
    scanners: PropTypes.arrayOf(PropTypes.shape(myTypes.scannerShape)),
    defaultExpanded: PropTypes.bool,
};

ProjectsRoot.defaultProps = {
    newExperiment: undefined,
    newExperimentErrors: undefined,
    newProject: null,
    newProjectErrors: null,
    projects: [],
    scanners: [],
    defaultExpanded: false,
};
