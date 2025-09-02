// This file contains the JavaScript code for the web application.
// It includes functionality such as event handling, DOM manipulation, and other interactive features.

document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('myButton');
    const output = document.getElementById('output');

    button.addEventListener('click', () => {
        output.textContent = 'Button was clicked!';
    });
});