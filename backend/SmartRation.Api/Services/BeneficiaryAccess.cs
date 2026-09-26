using SmartRation.Api.Models;

namespace SmartRation.Api.Services;

// THE rule for who may read a beneficiary's (or a family's) records — one place instead of the five
// copies it used to have. A citizen (RuralUser) sees only their own; staff roles see any.
//
// NOTE (open decision, see docs/PROJECT_AUDIT.md): ShopOwner currently sees ANY beneficiary, while
// search limits shop owners to their own shop. Tightening this needs a product decision first
// (e.g. One Nation One Ration Card portability lets a citizen collect at another shop).
public static class BeneficiaryAccess
{
    public static bool CanSee(ICurrentUserService user, int ownerUserId) => user.Role switch
    {
        UserRole.RuralUser => ownerUserId == user.UserId,
        UserRole.ShopOwner or UserRole.GovernmentOfficial or UserRole.Admin => true,
        _ => false
    };

    // A family is visible to a citizen when one of its beneficiary accounts is theirs.
    public static bool CanSeeFamily(ICurrentUserService user, IEnumerable<int> beneficiaryUserIds) => user.Role switch
    {
        UserRole.RuralUser => beneficiaryUserIds.Contains(user.UserId),
        UserRole.ShopOwner or UserRole.GovernmentOfficial or UserRole.Admin => true,
        _ => false
    };
}
