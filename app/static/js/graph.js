// Dependency Graph Visualization — Module 5
// Requires D3.js v7 loaded via CDN

class DependencyGraph {
    constructor(containerId, data) {
        this.containerId = containerId;
        this.data = data;
    }

    render() {
        // TODO: D3 force-directed graph
        console.log("Rendering graph in", this.containerId);
    }

    update(data) {
        // TODO: update with new data
        this.data = data;
        this.render();
    }

    highlightVulnerable(packageNames) {
        // TODO: highlight vulnerable nodes in red
        console.log("Highlighting vulnerable packages:", packageNames);
    }

    resize() {
        // TODO: responsive resize
        console.log("Resizing graph");
    }
}

if (typeof window !== 'undefined') {
    window.DependencyGraph = DependencyGraph;
}
