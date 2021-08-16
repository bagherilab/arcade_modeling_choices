// GLOBAL VARIABLES ============================================================

var PATH = "/analysis/"

var FONT_SIZE = 10

var FONT_PADDING = 4

var LABEL_SIZE = FONT_SIZE + 2*FONT_PADDING

var LABEL_PADDING = 3

var PANEL_PADDING = 4

var SUBPANEL_PADDING = 2

var AXIS_EMPTY = {
    "bottom": 0,
    "left": 0,
    "top": 0,
    "right": 0
}

var AXIS_PADDING = {
    "bottom": LABEL_SIZE + 5 + 2*FONT_PADDING + FONT_SIZE - 2,
    "left": LABEL_SIZE + 5 + 2*FONT_PADDING + (FONT_SIZE - 2)*2,
    "top": 0,
    "right": 0
}

var EXP = function(e) {
  return '<tspan baseline-shift="super" font-size="70%">' + e + '</tspan>'
}

var UNIT = function(e) {
    return '<tspan font-weight="normal" font-size="' + (FONT_SIZE - 2) + 'pt">(' + e + ')</tspan>'
}
var COLORMAPS = {
    "grayscale": ["#ddd", "#333"]
}

var COLORS = {
    "states": ["#dddddd", "#f00", "#bbbbbb", "#111111", "#666666", "#f00", "#f00"],
}

// GENERAL BEHAVIOR ============================================================

function initialize(id, plot) {
    // Attach event listeners to all inputs.
    for (let i = 0; i < OPTIONS.length; i++) {
        let e = document.getElementById(OPTIONS[i]).getElementsByTagName("INPUT")
        for (let j = 0; j < e.length; j++) { e[j].addEventListener("click", listen) }
        update(OPTIONS[i], e)
    }

    // Add event listeners for buttons.
    document.getElementById("generate").addEventListener("click", generate)
}

function listen() {
    let input = this.type
    let name = this.name
    let id = this.id.split("_")
    if (id.length == 3) { id[1] = id[1] + "_" + id[2] }

    // Update selection dictionary.
    if (input === "checkbox") { SELECTED.checks[id[0]][MAP[id[0]][id[1]]] = this.checked }
    else if (input === "radio") { SELECTED.radios[id[0]] = id[1] }
}

function update(id, e) {
    for (let i = 0; i < e.length; i++) {
        let eid = e[i].id.split("_")
        if (eid.length == 3) { eid[1] = eid[1] + "_" + eid[2] }

        if (e[i].type == "checkbox") {
            e[i].checked = SELECTED.checks[eid[0]][MAP[eid[0]][eid[1]]]
        } else if (e[i].type == "radio") {
            if (eid[1] === SELECTED.radios[eid[0]]) { e[i].checked = true }
        }
    }
}

// SVG GENERATOR ===============================================================

function generate() {
    clear()
    let P = PROCESSOR()

    // Create settings object.
    let S = {
        "id": "download",
        "width": SIZE.width,
        "height": SIZE.height,
        "margin": P.margin,
        "selected": P.selected,
        "layout": P.layout,
        "axis": P.axis
    }

    // Create SVG.
    S.SVG = d3.select("#canvas").append("svg")
        .attr("id", S.id)
        .attr("width", S.width)
        .attr("height", S.height)

    // Calculate size of figure and add offset group.
    S.W = S.width - S.margin.left - S.margin.right
    S.H = S.height - S.margin.top - S.margin.bottom
    S.G = S.SVG.append("g").attr("transform", translate(S.margin.left, S.margin.top))

    // Calculate panel layout.
    let pad = PANEL_PADDING
    let dw = S.W/P.cols
    let dh = S.H/P.rows
    S.panel = updateSettings(P, pad, dw, dh)

    // Call subgenerate on each subpanel.
    S.G.selectAll("g")
        .data(P.files).enter()
        .append("g")
            .attr("transform", d => translate(dw*d.x + pad/2, dh*d.y + pad/2))
            .attr("id", d => d.file)
            .each(function(pt, i) {
                let g = d3.select(this)

                // Load doubled files.
                let files = g.attr("id").split("~")
                if (files.length == 2) {
                    let file1 = PATH + files[0]
                    let file2 = PATH + files[1]

                    let file1Split = file1.split(".")
                    let file2Split = file2.split(".")

                    let file1Ext = file1Split[file1Split.length - 1]
                    let file2Ext = file2Split[file2Split.length - 1]

                    console.log(file1Split, file1Ext)

                    d3[file1Ext](file1, function(error1, data1) {
                        d3[file2Ext](file2, function(error2, data2) {
                            if (error1) { empty(g, file1, S.panel.w, S.panel.h) }
                            if (error2) { empty(g, file2, S.panel.w, S.panel.h) }
                            else { subgenerate(g, S, { "data1": data1, "data2": data2, "i": P.files[i].i }) }
                        })
                    })

                    return
                }

                let file = PATH + g.attr("id")
                file = file.replace(/-/g,"_")
                let split = file.split(".")
                let extension = split[split.length - 1]

                if (extension == "json") {
                    d3.json(file, function(error, data) {
                        if (error) { empty(g, file, S.panel.w, S.panel.h) }
                        else { subgenerate(g, S, { "data": data, "i": P.files[i].i }) }
                    })
                } else if (extension == "csv") {
                    d3.csv(file, function(error, data) {
                        if (error) { empty(g, file, S.panel.w, S.panel.h) }
                        else { subgenerate(g, S, { "data": data, "i": P.files[i].i }) }
                    })
                }
            })
        .call(() => addLabels(S.G, LABELLER(S, P)))
        .call(() => d3.select("#save").attr("disabled", null).on("click", () => saveAs(PREFIX)))
}

function subgenerate(g, S, d) {
    let id = g.attr("id")
    let P = PARSER(id, S, d)

    // Calculate subpanel layout.
    let pad = SUBPANEL_PADDING
    let dw = (S.panel.w - S.margin.axis.left - S.margin.axis.right)/P.cols
    let dh = (S.panel.h - S.margin.axis.top - S.margin.axis.bottom)/P.rows
    S.subpanel = updateSettings(P, pad, dw, dh)

    if (typeof S.axis.x === "function") {
        let keys = S.axis.keys
        S.xscale = {}
        keys.forEach(function(e) {
            let bounds = S.axis.x(e).bounds.map(e => e)
            bounds[0] = bounds[0] - (S.axis.x(e).padding ? S.axis.x(e).padding : 0)
            bounds[1] = bounds[1] + (S.axis.x(e).padding ? S.axis.x(e).padding : 0)
            S.xscale[e] = d3.scaleLinear().range([0, dw - pad]).domain(bounds)
        })
    } else {
        let bounds = S.axis.x.bounds.map(e => e)
        bounds[0] = bounds[0] - (S.axis.x.padding ? S.axis.x.padding : 0)
        bounds[1] = bounds[1] + (S.axis.x.padding ? S.axis.x.padding : 0)
        S.xscale = d3.scaleLinear().range([0, dw - pad]).domain(bounds)
    }

    if (typeof S.axis.y === "function") {
        let keys = S.axis.keys
        S.yscale = {}
        keys.forEach(function(e) {
            let bounds = S.axis.y(e).bounds.map(e => e)
            bounds[0] = bounds[0] - (S.axis.y(e).padding ? S.axis.y(e).padding : 0)
            bounds[1] = bounds[1] + (S.axis.y(e).padding ? S.axis.y(e).padding : 0)
            S.yscale[e] = d3.scaleLinear().range([dh - pad, 0]).domain(bounds)
        })
    } else {
        let bounds = S.axis.y.bounds.map(e => e)
        bounds[0] = bounds[0] - (S.axis.y.padding ? S.axis.y.padding : 0)
        bounds[1] = bounds[1] + (S.axis.y.padding ? S.axis.y.padding : 0)
        S.yscale = d3.scaleLinear().range([dh - pad, 0]).domain(bounds)
    }

    // Call subgenerate on each subpanel.
    g.selectAll("g")
        .data(P.data).enter()
        .append("g")
            .attr("transform", d => translate(dw*d.x + pad/2 + S.margin.axis.left, dh*d.y + pad/2 + S.margin.axis.top))
            .attr("id", d => id + "_" + d.id)
            .attr("clip-path", d => "url(#" + clip(id + "_" + d.id) + ")")
            .each(function(pt, i) {
                let g = d3.select(this)

                g.selectAll("g")
                    .data(d => d.data)
                    .enter().append("g")
                        .each(function(d) {
                            let f = "plot" + d["*"][0].toUpperCase() + d["*"].slice(1)
                            window[f](d3.select(this), S)
                        })

                DECORATOR(g, S, d.i, P.data[i])
            })
            .append("clipPath")
                .attr("id", d => clip(id + "_" + d.id))
                .append("rect")
                    .attr("width", dw - pad)
                    .attr("height", dh - pad)
}

// -----------------------------------------------------------------------------

function clear() {
    let node = document.getElementById("canvas")
    while (node.firstChild) {
        node.removeChild(node.firstChild)
    }
}

function translate(x, y) {
    return "translate(" + x + "," + y + ")"
}

function clip(id) {
    let id_split = id.split("/")
    return "clip-" + id_split[id_split.length - 1]
}

function empty(g, text, w, h) {
    let t = text.split("/")
    t = t[t.length - 1].replace(".csv","")

    g.append("rect")
        .attr("width", w)
        .attr("height", h)
        .attr("fill", "#999")
        .attr("stroke", "#555")
        .attr("opacity", 0.5)

    g.append("text")
        .text(t)
        .attr("x", w/2)
        .attr("y", h/2 + 5)
        .attr("font-family", "Courier")
        .attr("font-size", "10pt")
        .attr("fill", "#fff")
        .attr("text-anchor", "middle")
}

function updateSettings(P, pad, dw, dh) {
    return {
        "dw": dw,
        "dh": dh,
        "rows": P.rows,
        "cols": P.cols,
        "w": dw - pad,
        "h": dh - pad
    }
}
