import type { User } from "../types";

export function ProfilePage({ user }: { user: User }) {
  return <section>
    <div className="page-heading"><div><p className="eyebrow">Account</p><h1>Your profile</h1><p>Your account will own the cat profiles and observations you create.</p></div></div>
    <article className="card profile-card">
      <div className="profile-avatar">{user.display_name.charAt(0).toUpperCase()}</div>
      <div><h2>{user.display_name}</h2><p>{user.email}</p><span className="verified-badge">✓ Email confirmed</span></div>
    </article>
  </section>;
}
