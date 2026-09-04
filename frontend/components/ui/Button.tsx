import { ButtonHTMLAttributes, forwardRef } from "react";
import clsx from "clsx";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary";
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", isLoading, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={clsx(
          "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-60",
          variant === "primary" && "bg-slate-900 text-white hover:bg-slate-800",
          variant === "secondary" && "bg-slate-100 text-slate-900 hover:bg-slate-200",
          className
        )}
        {...props}
      >
        {isLoading ? "Please wait..." : children}
      </button>
    );
  }
);
Button.displayName = "Button";
