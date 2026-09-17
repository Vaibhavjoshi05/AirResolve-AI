"""
Script to generate high-resolution architecture diagram (architecture.png).
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

def create_architecture_diagram():
    fig, ax = plt.subplots(figsize=(14, 10), dpi=300)
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Color palette
    navy = "#0B192C"
    blue = "#1E3E62"
    accent_blue = "#008DDA"
    light_blue = "#E0F2FE"
    card_bg = "#FFFFFF"
    green = "#059669"
    red = "#DC2626"
    amber = "#D97706"
    border = "#CBD5E1"

    # Title Block
    ax.text(7, 9.5, "AirResolve: System Architecture & Decision Flow", 
            ha='center', va='center', fontsize=18, fontweight='bold', color=navy)
    ax.text(7, 9.15, "Policy-Grounded Airline Disruption Resolution Agent (Assignment 3 Source of Truth)", 
            ha='center', va='center', fontsize=11, color='#64748B')

    # 1. User Layer
    rect_user = patches.FancyBboxPatch((5.0, 8.0), 4.0, 0.75, boxstyle="round,pad=0.1,rounding_size=0.15", 
                                       facecolor=navy, edgecolor=navy, linewidth=1.5)
    ax.add_patch(rect_user)
    ax.text(7.0, 8.375, "USER / PASSENGER (Web & Mobile Chat)", ha='center', va='center', 
            fontsize=11, fontweight='bold', color='white')

    # Arrow User -> UI
    ax.annotate("", xy=(7.0, 7.3), xytext=(7.0, 8.0),
                arrowprops=dict(arrowstyle="->", lw=2, color=accent_blue))

    # 2. UI Layer
    rect_ui = patches.FancyBboxPatch((3.0, 6.4), 8.0, 0.9, boxstyle="round,pad=0.1,rounding_size=0.15", 
                                     facecolor=card_bg, edgecolor=border, linewidth=1.5)
    ax.add_patch(rect_ui)
    ax.text(7.0, 6.95, "STREAMLIT PRESENTATION LAYER (AirResolve UI)", ha='center', va='center', 
            fontsize=12, fontweight='bold', color=navy)
    ax.text(7.0, 6.6, "Passenger Selector • Live Flight Status • Chat Interface • Action Chips • Decision Audit Trace", 
            ha='center', va='center', fontsize=9.5, color='#475569')

    # Arrow UI -> Orchestrator
    ax.annotate("", xy=(7.0, 5.7), xytext=(7.0, 6.4),
                arrowprops=dict(arrowstyle="->", lw=2, color=accent_blue))

    # 3. Conversational Layer
    rect_agent = patches.FancyBboxPatch((3.0, 4.8), 8.0, 0.9, boxstyle="round,pad=0.1,rounding_size=0.15", 
                                        facecolor=light_blue, edgecolor=accent_blue, linewidth=1.5)
    ax.add_patch(rect_agent)
    ax.text(7.0, 5.35, "CONVERSATIONAL ORCHESTRATOR & INTENT ROUTER", ha='center', va='center', 
            fontsize=12, fontweight='bold', color=blue)
    ax.text(7.0, 5.0, "Entity Extraction • Dialogue History • Sentiment / Frustration Detection • Response Generator", 
            ha='center', va='center', fontsize=9.5, color='#0369A1')

    # Downward split arrows: Data Pack (Left) & Deterministic Policy Engine (Right)
    ax.annotate("", xy=(3.5, 4.1), xytext=(5.5, 4.8),
                arrowprops=dict(arrowstyle="->", lw=2, color='#64748B'))
    ax.annotate("", xy=(10.5, 4.1), xytext=(8.5, 4.8),
                arrowprops=dict(arrowstyle="->", lw=2, color='#64748B'))

    # 4. Data Repository (Left Box)
    rect_data = patches.FancyBboxPatch((0.8, 2.7), 5.0, 1.4, boxstyle="round,pad=0.1,rounding_size=0.15", 
                                       facecolor=card_bg, edgecolor=border, linewidth=1.5)
    ax.add_patch(rect_data)
    ax.text(3.3, 3.85, "DATA REPOSITORY (Source of Truth)", ha='center', va='center', 
            fontsize=11, fontweight='bold', color=navy)
    ax.text(3.3, 3.45, "• Customers: Priya (Gold), Arvind (Silver), Meher (Plat)\n• Bookings: SK-204, SK-118, SK-305\n• Flight Status: Cancelled, 4h Delay, 6h Delay", 
            ha='center', va='center', fontsize=9, color='#334155')

    # 5. Deterministic Policy Engine (Right Box) - HIGHLIGHTED AS SINGLE SOURCE OF TRUTH
    rect_policy = patches.FancyBboxPatch((8.2, 2.7), 5.0, 1.4, boxstyle="round,pad=0.1,rounding_size=0.15", 
                                         facecolor='#FEF3C7', edgecolor=amber, linewidth=2.0)
    ax.add_patch(rect_policy)
    ax.text(10.7, 3.85, "DETERMINISTIC POLICY ENGINE", ha='center', va='center', 
            fontsize=11, fontweight='bold', color='#92400E')
    ax.text(10.7, 3.45, "• Cancellation & 24h Rebooking / Refund Rule\n• Delay Compensation: <3h, 3h-5h, >5h (Hotel rule)\n• Fare Difference Waiver Limit: <= ₹1,500\n• Loyalty Rules: Priority seat access, no extra comp", 
            ha='center', va='center', fontsize=8.5, color='#78350F')

    # Converge arrows into Decision Engine
    ax.annotate("", xy=(6.0, 2.2), xytext=(4.0, 2.7),
                arrowprops=dict(arrowstyle="->", lw=2, color='#64748B'))
    ax.annotate("", xy=(8.0, 2.2), xytext=(10.0, 2.7),
                arrowprops=dict(arrowstyle="->", lw=2, color='#64748B'))

    # 6. Decision & Guardrail Layer
    rect_dec = patches.FancyBboxPatch((3.5, 1.5), 7.0, 0.7, boxstyle="round,pad=0.1,rounding_size=0.15", 
                                      facecolor=card_bg, edgecolor=navy, linewidth=1.5)
    ax.add_patch(rect_dec)
    ax.text(7.0, 1.85, "POLICY DECISION & COMPLIANCE GATEWAY", ha='center', va='center', 
            fontsize=11, fontweight='bold', color=navy)

    # 3 Outcome branches
    # Branch 1: Resolve
    ax.annotate("", xy=(2.5, 0.9), xytext=(5.0, 1.5),
                arrowprops=dict(arrowstyle="->", lw=2, color=green))
    rect_res = patches.FancyBboxPatch((1.0, 0.2), 3.0, 0.7, boxstyle="round,pad=0.1,rounding_size=0.1", 
                                      facecolor='#ECFDF5', edgecolor=green, linewidth=1.5)
    ax.add_patch(rect_res)
    ax.text(2.5, 0.55, "RESOLVE (Policy Applied)", ha='center', va='center', 
            fontsize=10, fontweight='bold', color=green)
    ax.text(2.5, 0.35, "Issue Vouchers / Refund / Rebook", ha='center', va='center', 
            fontsize=8, color='#065F46')

    # Branch 2: Clarify / Ineligible
    ax.annotate("", xy=(7.0, 0.9), xytext=(7.0, 1.5),
                arrowprops=dict(arrowstyle="->", lw=2, color=amber))
    rect_clar = patches.FancyBboxPatch((5.5, 0.2), 3.0, 0.7, boxstyle="round,pad=0.1,rounding_size=0.1", 
                                       facecolor='#FFFBEB', edgecolor=amber, linewidth=1.5)
    ax.add_patch(rect_clar)
    ax.text(7.0, 0.55, "CLARIFY / INELIGIBLE", ha='center', va='center', 
            fontsize=10, fontweight='bold', color=amber)
    ax.text(7.0, 0.35, "Offer Choice / Explain Policy Scope", ha='center', va='center', 
            fontsize=8, color='#92400E')

    # Branch 3: Escalate
    ax.annotate("", xy=(11.5, 0.9), xytext=(9.0, 1.5),
                arrowprops=dict(arrowstyle="->", lw=2, color=red))
    rect_esc = patches.FancyBboxPatch((10.0, 0.2), 3.0, 0.7, boxstyle="round,pad=0.1,rounding_size=0.1", 
                                      facecolor='#FEF2F2', edgecolor=red, linewidth=1.5)
    ax.add_patch(rect_esc)
    ax.text(11.5, 0.55, "ESCALATE (Human Review)", ha='center', va='center', 
            fontsize=10, fontweight='bold', color=red)
    ax.text(11.5, 0.35, "Supervisor Ticket / Legal Transfer", ha='center', va='center', 
            fontsize=8, color='#991B1B')

    # Important Guardrail Callout Banner
    callout = patches.FancyBboxPatch((0.8, 9.0), 4.2, 0.7, boxstyle="round,pad=0.08,rounding_size=0.1", 
                                     facecolor='#EFF6FF', edgecolor='#3B82F6', linewidth=1)
    ax.add_patch(callout)
    ax.text(2.9, 9.35, "STRICT ARCHITECTURAL PRINCIPLE", ha='center', va='center', 
            fontsize=8.5, fontweight='bold', color='#1E40AF')
    ax.text(2.9, 9.15, "Conversational LLM CANNOT override deterministic policy", ha='center', va='center', 
            fontsize=7.5, color='#1D4ED8')

    out_path = os.path.join(os.path.dirname(__file__), "architecture.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Architecture diagram successfully saved to: {out_path}")

if __name__ == "__main__":
    create_architecture_diagram()
