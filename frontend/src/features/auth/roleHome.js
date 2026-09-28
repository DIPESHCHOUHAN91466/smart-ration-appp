export function homePathForRole(role) {
  if (role === "RuralUser") return "/rural/dashboard";
  if (role === "ShopOwner") return "/shop/dashboard";
  if (role === "GovernmentOfficial" || role === "Admin") return "/gov/dashboard";
  return "/login";
}
