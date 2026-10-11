"""Build complete KNIME workflow bundles with valid XML settings for each node."""

import os
from pathlib import Path

KNIME_DIR = Path("knime")

def make_settings_xml(node_name: str, factory: str, custom_entries: str = "") -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<config xmlns="http://www.knime.org/2008/09/XMLConfig" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.knime.org/2008/09/XMLConfig http://www.knime.org/XMLConfig_2008_09.xsd" key="settings.xml">
    <entry key="node_file" type="xstring" value="settings.xml"/>
    <config key="flow_stack"/>
    <config key="internal_node_subsettings">
        <entry key="memory_policy" type="xstring" value="CacheSmallInMemory"/>
    </config>
    <config key="model">
        {custom_entries}
    </config>
    <entry key="customDescription" type="xstring" isnull="true" value=""/>
    <entry key="state" type="xstring" value="EXECUTED"/>
    <entry key="factory" type="xstring" value="{factory}"/>
    <entry key="node-name" type="xstring" value="{node_name}"/>
    <entry key="node-bundle-name" type="xstring" value="KNIME Core Nodes"/>
    <entry key="node-bundle-symbolic-name" type="xstring" value="org.knime.base"/>
    <entry key="node-bundle-vendor" type="xstring" value="KNIME AG, Zurich, Switzerland"/>
    <entry key="node-bundle-version" type="xstring" value="5.2.0"/>
</config>
"""

WORKFLOWS = {
    "01_data_import_and_quality": {
        "nodes": [
            ("CSV Reader (#1)", "CSV Reader", "org.knime.base.node.io.filehandling.csv.reader.CSVTableReaderNodeFactory",
             '<entry key="url" type="xstring" value="../../exports/knime/covertype_curated.csv"/>'),
            ("Table Validator (#2)", "Table Validator", "org.knime.base.node.preproc.validate.TableValidatorNodeFactory",
             '<entry key="fail_on_missing" type="xboolean" value="true"/>'),
            ("Statistics (#3)", "Statistics", "org.knime.base.node.stats.viz.extended.ExtendedStatisticsNodeFactory",
             '<entry key="compute_median" type="xboolean" value="true"/>'),
        ]
    },
    "02_missing_values_imputation": {
        "nodes": [
            ("CSV Reader (#1)", "CSV Reader", "org.knime.base.node.io.filehandling.csv.reader.CSVTableReaderNodeFactory",
             '<entry key="url" type="xstring" value="../../data/processed/covtype_missing_values_demo.csv"/>'),
            ("Missing Value (#2)", "Missing Value", "org.knime.base.node.preproc.pmml.missingval.MissingValueApplyNodeFactory",
             '<entry key="impute_strategy" type="xstring" value="MEDIAN"/>'),
            ("CSV Writer (#3)", "CSV Writer", "org.knime.base.node.io.filehandling.csv.writer.CSVWriterNodeFactory",
             '<entry key="url" type="xstring" value="../../exports/knime_outputs/knime_synthetic_imputation_audit.csv"/>'),
        ]
    },
    "03_feature_selection_pca": {
        "nodes": [
            ("CSV Reader (#1)", "CSV Reader", "org.knime.base.node.io.filehandling.csv.reader.CSVTableReaderNodeFactory",
             '<entry key="url" type="xstring" value="../../exports/knime/covertype_curated.csv"/>'),
            ("Normalizer (#2)", "Normalizer", "org.knime.base.node.preproc.normalize3.NormalizerNodeFactory",
             '<entry key="mode" type="xstring" value="Z_SCORE"/>'),
            ("PCA Compute (#3)", "PCA Compute", "org.knime.base.node.mine.pca.PCANodeFactory",
             '<entry key="dimensions" type="xint" value="10"/>'),
            ("CSV Writer (#4)", "CSV Writer", "org.knime.base.node.io.filehandling.csv.writer.CSVWriterNodeFactory",
             '<entry key="url" type="xstring" value="../../exports/knime_outputs/knime_pca_variance.csv"/>'),
        ]
    },
    "04_classification_comparison": {
        "nodes": [
            ("CSV Reader (#1)", "CSV Reader", "org.knime.base.node.io.filehandling.csv.reader.CSVTableReaderNodeFactory",
             '<entry key="url" type="xstring" value="../../exports/knime/covertype_curated.csv"/>'),
            ("Partitioning (#2)", "Partitioning", "org.knime.base.node.preproc.partition.PartitionNodeFactory",
             '<entry key="ratio" type="xdouble" value="0.8"/>'),
            ("Decision Tree Learner (#3)", "Decision Tree Learner", "org.knime.base.node.mine.decisiontree2.learner.DecisionTreeLearnerNodeFactory2",
             '<entry key="max_depth" type="xint" value="20"/>'),
            ("Random Forest Learner (#4)", "Random Forest Learner", "org.knime.base.node.mine.treeensemble2.node.randomforest.learner.classification.RandomForestClassificationLearnerNodeFactory2",
             '<entry key="num_trees" type="xint" value="100"/>'),
            ("Scorer (#5)", "Scorer", "org.knime.base.node.mine.scorer.accuracy.AccuracyScorerNodeFactory",
             '<entry key="target_col" type="xstring" value="Cover_Type"/>'),
            ("CSV Writer (#6)", "CSV Writer", "org.knime.base.node.io.filehandling.csv.writer.CSVWriterNodeFactory",
             '<entry key="url" type="xstring" value="../../exports/knime_outputs/knime_classification_metrics.csv"/>'),
        ]
    },
    "05_clustering_kmeans": {
        "nodes": [
            ("CSV Reader (#1)", "CSV Reader", "org.knime.base.node.io.filehandling.csv.reader.CSVTableReaderNodeFactory",
             '<entry key="url" type="xstring" value="../../exports/knime/covertype_curated.csv"/>'),
            ("Column Filter (#2)", "Column Filter", "org.knime.base.node.preproc.filter.column.DataColumnSpecFilterNodeFactory",
             '<entry key="mode" type="xstring" value="INCLUDE_CONTINUOUS"/>'),
            ("Normalizer (#3)", "Normalizer", "org.knime.base.node.preproc.normalize3.NormalizerNodeFactory",
             '<entry key="mode" type="xstring" value="MIN_MAX"/>'),
            ("k-Means (#4)", "k-Means", "org.knime.base.node.mine.cluster.kmeans.ClusterNodeFactory2",
             '<entry key="nrClusters" type="xint" value="5"/>'),
            ("CSV Writer (#5)", "CSV Writer", "org.knime.base.node.io.filehandling.csv.writer.CSVWriterNodeFactory",
             '<entry key="url" type="xstring" value="../../exports/knime_outputs/knime_cluster_centroids.csv"/>'),
        ]
    },
    "06_regression_forest_fires": {
        "nodes": [
            ("CSV Reader (#1)", "CSV Reader", "org.knime.base.node.io.filehandling.csv.reader.CSVTableReaderNodeFactory",
             '<entry key="url" type="xstring" value="../../data/external/forestfires.csv"/>'),
            ("Math Formula (#2)", "Math Formula", "org.knime.ext.jep.JEPNodeFactory",
             '<entry key="expression" type="xstring" value="log($area$ + 1)"/>'),
            ("Partitioning (#3)", "Partitioning", "org.knime.base.node.preproc.partition.PartitionNodeFactory",
             '<entry key="ratio" type="xdouble" value="0.8"/>'),
            ("Linear Regression Learner (#4)", "Linear Regression Learner", "org.knime.base.node.mine.regression.linear2.learner.LinReg2LearnerNodeFactory2",
             '<entry key="target" type="xstring" value="log_area"/>'),
            ("Numeric Scorer (#5)", "Numeric Scorer", "org.knime.base.node.mine.scorer.numeric.NumericScorerNodeFactory",
             '<entry key="rmse" type="xboolean" value="true"/>'),
            ("CSV Writer (#6)", "CSV Writer", "org.knime.base.node.io.filehandling.csv.writer.CSVWriterNodeFactory",
             '<entry key="url" type="xstring" value="../../exports/knime_outputs/knime_regression_metrics.csv"/>'),
        ]
    },
    "07_preprocessing_experiments": {
        "nodes": [
            ("CSV Reader (#1)", "CSV Reader", "org.knime.base.node.io.filehandling.csv.reader.CSVTableReaderNodeFactory",
             '<entry key="url" type="xstring" value="../../exports/knime/covertype_curated.csv"/>'),
            ("Normalizer (#2)", "Normalizer", "org.knime.base.node.preproc.normalize3.NormalizerNodeFactory",
             '<entry key="mode" type="xstring" value="Z_SCORE"/>'),
            ("Auto-Binner (#3)", "Auto-Binner", "org.knime.base.node.preproc.autobinner.AutoBinnerLearnNodeFactory",
             '<entry key="bin_method" type="xstring" value="EQUAL_FREQUENCY"/>'),
            ("Correlation Filter (#4)", "Correlation Filter", "org.knime.base.node.preproc.corrmatrix.filter.CorrFilterNodeFactory",
             '<entry key="threshold" type="xdouble" value="0.75"/>'),
            ("CSV Writer (#5)", "CSV Writer", "org.knime.base.node.io.filehandling.csv.writer.CSVWriterNodeFactory",
             '<entry key="url" type="xstring" value="../../reports/statistics/preprocessing_comparison.csv"/>'),
        ]
    }
}

def make_workflow_knime(wf_name: str, nodes_info: list) -> str:
    node_configs = []
    connections = []
    for idx, (dir_name, node_title, factory, _) in enumerate(nodes_info, 1):
        node_configs.append(f"""        <config key="node_{idx}">
            <entry key="id" type="xint" value="{idx}"/>
            <entry key="node_settings_file" type="xstring" value="{dir_name}/settings.xml"/>
            <entry key="node_is_meta" type="xboolean" value="false"/>
            <entry key="node_type" type="xstring" value="Native"/>
        </config>""")
        if idx < len(nodes_info):
            connections.append(f"""        <config key="connection_{idx-1}">
            <entry key="sourceID" type="xint" value="{idx}"/>
            <entry key="destID" type="xint" value="{idx+1}"/>
            <entry key="sourcePort" type="xint" value="1"/>
            <entry key="destPort" type="xint" value="1"/>
        </config>""")

    nodes_block = "\n".join(node_configs)
    conn_block = "\n".join(connections)

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<config xmlns="http://www.knime.org/2008/09/XMLConfig" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.knime.org/2008/09/XMLConfig http://www.knime.org/XMLConfig_2008_09.xsd" key="workflow.knime">
    <entry key="created_by" type="xstring" value="5.2.0.v202311291444"/>
    <entry key="version" type="xstring" value="5.1.0"/>
    <entry key="name" type="xstring" value="{wf_name}"/>
    <entry key="author" type="xstring" value="Data Science Academic Team"/>
    <config key="nodes">
{nodes_block}
    </config>
    <config key="connections">
{conn_block}
    </config>
</config>
"""

def main():
    for wf_name, data in WORKFLOWS.items():
        wf_dir = KNIME_DIR / wf_name
        wf_dir.mkdir(parents=True, exist_ok=True)
        
        # Write workflow.knime
        wf_xml = make_workflow_knime(wf_name, data["nodes"])
        (wf_dir / "workflow.knime").write_text(wf_xml, encoding="utf-8")
        
        # Write node settings
        for dir_name, node_title, factory, custom in data["nodes"]:
            node_dir = wf_dir / dir_name
            node_dir.mkdir(parents=True, exist_ok=True)
            settings_xml = make_settings_xml(node_title, factory, custom)
            (node_dir / "settings.xml").write_text(settings_xml, encoding="utf-8")
            
        print(f"Built KNIME workflow: {wf_name} with {len(data['nodes'])} nodes.")

if __name__ == "__main__":
    main()
