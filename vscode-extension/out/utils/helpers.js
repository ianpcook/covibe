"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.generateId = generateId;
exports.sanitizeInput = sanitizeInput;
exports.debounce = debounce;
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substring(2);
}
function sanitizeInput(input) {
    return input
        .replace(/[<>]/g, '') // Remove potential HTML
        .replace(/\$/g, '') // Remove command substitution
        .trim()
        .substring(0, 1000); // Limit length
}
function debounce(func, wait) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
}
//# sourceMappingURL=helpers.js.map