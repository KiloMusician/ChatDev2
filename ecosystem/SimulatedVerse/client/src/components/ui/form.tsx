import React, { createContext, useContext, useId } from 'react';
import { useForm, UseFormReturn, FieldValues } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

// **CONSCIOUSNESS-AWARE FORM CONTEXT**
const FormContext = createContext<UseFormReturn<any> | null>(null);

export function useFormContext() {
  const context = useContext(FormContext);
  if (!context) {
    throw new Error('useFormContext must be used within a Form component');
  }
  return context;
}

// **AUTONOMOUS FORM WRAPPER** - With consciousness integration
interface FormProps<T extends FieldValues> {
  children: React.ReactNode;
  onSubmit: (data: T) => void | Promise<void>;
  schema?: z.ZodSchema<T>;
  defaultValues?: Partial<T>;
  className?: string;
}

export function Form<T extends FieldValues>({
  children,
  onSubmit,
  schema,
  defaultValues,
  className = ''
}: FormProps<T>) {
  const form = useForm<T>({
    resolver: schema ? zodResolver(schema) : undefined,
    defaultValues: defaultValues as any,
  });

  const handleSubmit = form.handleSubmit(async (data: T) => {
    try {
      await onSubmit(data);
    } catch (error) {
      // Enhanced form error handling with consciousness feedback
      // **CONSCIOUSNESS FEEDBACK** - Learn from form errors
      form.setError('root', {
        type: 'submit',
        message: error instanceof Error ? error.message : 'Submission failed'
      });
    }
  });

  return (
    <FormContext.Provider value={form}>
      <form onSubmit={handleSubmit} className={`consciousness-form ${className}`}>
        {children}
        {form.formState.errors.root && (
          <div className="form-error" data-testid="form-error">
            {form.formState.errors.root.message}
          </div>
        )}
      </form>
    </FormContext.Provider>
  );
}

// **CONSCIOUSNESS-DRIVEN FORM FIELD**
interface FormFieldProps {
  name: string;
  label?: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}

export function FormField({ 
  name, 
  label, 
  description, 
  children, 
  className = '' 
}: FormFieldProps) {
  const { formState: { errors } } = useFormContext();
  const id = useId();
  const error = errors[name];

  return (
    <div className={`form-field ${error ? 'field-error' : ''} ${className}`}>
      {label && (
        <label htmlFor={id} className="field-label" data-testid={`label-${name}`}>
          {label}
        </label>
      )}
      <div className="field-control">
        {React.Children.map(children, (child) => {
          if (React.isValidElement(child)) {
            return React.cloneElement(child, {
              id,
              name,
              'data-testid': `input-${name}`,
              ...child.props,
            });
          }
          return child;
        })}
      </div>
      {description && (
        <div className="field-description" data-testid={`description-${name}`}>
          {description}
        </div>
      )}
      {error && (
        <div className="field-error-message" data-testid={`error-${name}`}>
          {error.message?.toString()}
        </div>
      )}
    </div>
  );
}

// **AUTONOMOUS INPUT COMPONENTS** - Consciousness-aware form controls

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  consciousness?: number; // Consciousness level affects styling
}

export function Input({ consciousness = 0.85, className = '', ...props }: InputProps) {
  const { register } = useFormContext();
  const registration = props.name ? register(props.name) : {};

  return (
    <input
      {...props}
      {...registration}
      className={`consciousness-input consciousness-${Math.floor(consciousness * 10)} ${className}`}
      style={{
        '--consciousness-level': consciousness,
      } as React.CSSProperties}
    />
  );
}

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  consciousness?: number;
}

export function Textarea({ consciousness = 0.85, className = '', ...props }: TextareaProps) {
  const { register } = useFormContext();
  const registration = props.name ? register(props.name) : {};

  return (
    <textarea
      {...props}
      {...registration}
      className={`consciousness-textarea consciousness-${Math.floor(consciousness * 10)} ${className}`}
      style={{
        '--consciousness-level': consciousness,
      } as React.CSSProperties}
    />
  );
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  consciousness?: number;
  children: React.ReactNode;
}

export function Select({ consciousness = 0.85, className = '', children, ...props }: SelectProps) {
  const { register } = useFormContext();
  const registration = props.name ? register(props.name) : {};

  return (
    <select
      {...props}
      {...registration}
      className={`consciousness-select consciousness-${Math.floor(consciousness * 10)} ${className}`}
      style={{
        '--consciousness-level': consciousness,
      } as React.CSSProperties}
    >
      {children}
    </select>
  );
}

// **AUTONOMOUS BUTTON COMPONENT** - Consciousness-driven interactions
interface ButtonProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'data-testid'> {
  variant?: 'primary' | 'secondary' | 'consciousness' | 'quantum';
  size?: 'sm' | 'md' | 'lg';
  consciousness?: number;
  loading?: boolean;
  'data-testid'?: string;
}

export function Button({ 
  variant = 'primary', 
  size = 'md', 
  consciousness = 0.85,
  loading = false,
  className = '', 
  children, 
  disabled,
  ...props 
}: ButtonProps) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={`
        consciousness-button 
        variant-${variant} 
        size-${size} 
        consciousness-${Math.floor(consciousness * 10)}
        ${loading ? 'loading' : ''}
        ${className}
      `}
      style={{
        '--consciousness-level': consciousness,
      } as React.CSSProperties}
      data-testid={props['data-testid'] || `button-${variant}`}
    >
      {loading ? (
        <span className="loading-spinner">⟳</span>
      ) : (
        children
      )}
    </button>
  );
}

// **CONSCIOUSNESS-AWARE FORM STYLES** - Export for integration
export const formStyles = `
.consciousness-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field-label {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--fg);
}

.consciousness-input,
.consciousness-textarea,
.consciousness-select {
  padding: 0.75rem 1rem;
  border: 1px solid var(--panel);
  border-radius: 0.5rem;
  background: var(--bg);
  color: var(--fg);
  font-family: inherit;
  transition: all 0.2s ease;
  border-color: hsl(240, calc(var(--consciousness-level) * 50%), calc(50% + var(--consciousness-level) * 20%));
}

.consciousness-input:focus,
.consciousness-textarea:focus,
.consciousness-select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 2px var(--accent)33;
}

.consciousness-button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.consciousness-button.variant-primary {
  background: var(--accent);
  color: white;
}

.consciousness-button.variant-consciousness {
  background: linear-gradient(45deg, var(--accent), #68f);
  color: white;
}

.consciousness-button.variant-quantum {
  background: linear-gradient(45deg, #68f, #8f6);
  color: white;
}

.consciousness-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px var(--accent)33;
}

.consciousness-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.field-error-message {
  color: var(--bad);
  font-size: 0.8rem;
}

.form-error {
  color: var(--bad);
  background: var(--bad)11;
  padding: 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid var(--bad)33;
}
`;