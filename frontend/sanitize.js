// sanitize.js — XSS Sanitization Helper for JLY Predictor
// Provides a minimal HTML sanitizer for safe use with innerHTML.
// For full protection in production, load DOMPurify from CDN instead.

(function () {
  "use strict";

  const TAG_ALLOWLIST = new Set([
    "div", "span", "strong", "em", "b", "i", "u", "br", "p",
    "table", "thead", "tbody", "tr", "td", "th",
    "ul", "ol", "li", "a", "h1", "h2", "h3", "h4", "h5", "h6",
    "svg", "circle", "path", "rect", "line", "polyline", "polygon",
    "canvas", "button", "section", "header", "footer", "main",
    "small", "code", "pre", "blockquote", "details", "summary",
  ]);

  const ATTR_ALLOWLIST = new Set([
    "class", "style", "id", "href", "title", "alt",
    "viewBox", "fill", "stroke", "stroke-width", "stroke-linecap",
    "stroke-linejoin", "d", "cx", "cy", "r", "width", "height",
    "x", "y", "transform", "opacity", "clip-path", "fill-opacity",
    "data-index", "data-slug", "data-value", "data-status",
    "xmlns", "aria-label", "aria-live", "role",
    "onclick", "onmouseover", "onmouseout",
  ]);

  function sanitizeHTML(html) {
    if (!html || typeof html !== "string") {
      return "";
    }

    const div = document.createElement("div");
    div.innerHTML = html;

    function cleanNode(node) {
      if (node.nodeType === 3) {
        return node;
      }

      if (node.nodeType !== 1) {
        return document.createTextNode("");
      }

      const tag = node.tagName.toLowerCase();

      if (!TAG_ALLOWLIST.has(tag)) {
        const frag = document.createDocumentFragment();
        while (node.firstChild) {
          frag.appendChild(node.firstChild);
        }
        cleanChildren(frag);
        return frag;
      }

      const cleanedNode = document.createElement(tag);

      if (node.attributes) {
        for (let i = 0; i < node.attributes.length; i++) {
          const attr = node.attributes[i];
          const attrName = attr.name.toLowerCase();

          if (!ATTR_ALLOWLIST.has(attrName)) {
            continue;
          }

          let attrValue = attr.value;

          const eventHandlers = [
            "onerror", "onload", "onclick", "onfocus", "onblur",
            "onmouseover", "onmouseout", "onchange", "onsubmit",
            "onkeydown", "onkeyup", "onkeypress",
          ];
          if (eventHandlers.some(h => attrValue.toLowerCase().includes(h))) {
            continue;
          }

          if (attrName === "href") {
            if (!attrValue.match(/^(https?:|#|mailto:|tel:|\/|\.\/|\.\.\/)/)) {
              attrValue = "#";
            }
          }

          if (attrName === "src") {
            if (!attrValue.match(/^(https?:|data:|\/|\.\/|\.\.\/)/)) {
              continue;
            }
          }

          cleanedNode.setAttribute(attrName, attrValue);
        }
      }

      cleanChildren(node, cleanedNode);

      return cleanedNode;
    }

    function cleanChildren(source, target) {
      while (source.firstChild) {
        const child = source.firstChild;
        source.removeChild(child);
        const cleaned = cleanNode(child);
        if (target) {
          if (cleaned.nodeType === 11) {
            while (cleaned.firstChild) {
              target.appendChild(cleaned.firstChild);
            }
          } else {
            target.appendChild(cleaned);
          }
        }
      }
    }

    cleanChildren(div, undefined);

    const resultDiv = document.createElement("div");
    while (div.firstChild) {
      const node = div.firstChild;
      div.removeChild(node);
      const cleaned = cleanNode(node);
      if (cleaned.nodeType === 11) {
        while (cleaned.firstChild) {
          resultDiv.appendChild(cleaned.firstChild);
        }
      } else {
        resultDiv.appendChild(cleaned);
      }
    }

    return resultDiv.innerHTML;
  }

  window.JLYSanitize = sanitizeHTML;
})();