// Minimal ambient module declaration to satisfy TS compile in environments
// where @types/nodemailer is not installed (e.g., production installs).
declare module "nodemailer";