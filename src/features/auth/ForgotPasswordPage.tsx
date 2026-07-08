import { useState } from "react";
import { Link } from "react-router-dom";
import { Mail } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { authApi } from "@/api/auth";
import { RailMadadLogo } from "@/components/branding/RailMadadLogo";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Spinner } from "@/components/ui/Spinner";

const forgotSchema = z.object({
  email: z.string().email("Enter a valid email address"),
});

type ForgotFormData = z.infer<typeof forgotSchema>;

export function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotFormData>({
    resolver: zodResolver(forgotSchema),
  });

  const onSubmit = async (data: ForgotFormData) => {
    setError(null);
    try {
      await authApi.forgotPassword({ email: data.email });
      setSubmitted(true);
    } catch {
      setError("Unable to process request. Please try again.");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-4 py-16">
      <div className="w-full max-w-[400px] space-y-8">
        <div className="flex flex-col items-center text-center">
          <RailMadadLogo size="lg" />
          <h1 className="mt-6 text-2xl font-semibold tracking-tight text-slate-900">
            Reset Password
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Enter your account email to receive reset instructions
          </p>
        </div>

        <Card className="hover:shadow-card">
          <CardHeader className="pb-2">
            <CardTitle>Forgot password</CardTitle>
            <CardDescription>
              If an account exists for this email, you will receive a reset link.
            </CardDescription>
          </CardHeader>
          <CardBody>
            {submitted ? (
              <div className="space-y-4">
                <Alert variant="success">
                  If your email is registered, reset instructions have been sent.
                </Alert>
                <Link to="/login" className="block text-center text-sm text-primary hover:underline">
                  Back to sign in
                </Link>
              </div>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                {error && <Alert variant="error">{error}</Alert>}

                <div className="space-y-1.5">
                  <Label htmlFor="email">Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                    <Input
                      id="email"
                      type="email"
                      className="h-11 rounded-lg pl-10"
                      placeholder="you@example.com"
                      {...register("email")}
                    />
                  </div>
                  {errors.email && <p className="text-xs text-red-600">{errors.email.message}</p>}
                </div>

                <Button type="submit" className="h-11 w-full" disabled={isSubmitting}>
                  {isSubmitting ? <Spinner size="sm" /> : "Send reset link"}
                </Button>

                <p className="text-center text-sm text-slate-500">
                  <Link to="/login" className="text-primary hover:underline">
                    Back to sign in
                  </Link>
                </p>
              </form>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
