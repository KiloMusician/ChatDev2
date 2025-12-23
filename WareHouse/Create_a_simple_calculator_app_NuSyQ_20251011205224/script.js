/**
 * Calculator functions to perform basic arithmetic operations.
 */
// Function to add two numbers
function add(a, b) {
    return a + b;
}
// Function to subtract two numbers
function subtract(a, b) {
    return a - b;
}
// Function to multiply two numbers
function multiply(a, b) {
    return a * b;
}
// Function to divide two numbers
function divide(a, b) {
    if (b === 0) {
        throw new Error("Division by zero is not allowed.");
    }
    return a / b;
}
/**
 * Main function to handle user input and display the result.
 */
function calculate(operation) {
    const num1 = parseFloat(document.getElementById('num1').value);
    const num2 = parseFloat(document.getElementById('num2').value);
    // Validate inputs
    if (isNaN(num1) || isNaN(num2)) {
        document.getElementById('result').innerText = "Please enter valid numbers.";
        return;
    }
    let result;
    try {
        switch (operation) {
            case 'add':
                result = add(num1, num2);
                break;
            case 'subtract':
                result = subtract(num1, num2);
                break;
            case 'multiply':
                result = multiply(num1, num2);
                break;
            case 'divide':
                result = divide(num1, num2);
                break;
            default:
                throw new Error("Invalid operation.");
        }
    } catch (error) {
        document.getElementById('result').innerText = error.message;
        return;
    }
    // Display the result
    document.getElementById('result').innerText = `Result: ${result}`;
}